import hashlib
import hmac
import json
import os
import time
import uuid
import base64
import urllib.parse

import httpx

from app.config import settings


def _make_transcript() -> str:
    """Generate a mock transcript for development when no real audio is available."""
    return (
        "大家好，欢迎来到 PyGrow Python 学习课堂。"
        "本节课我们将学习 Python 编程的核心知识点。"
        "首先，让我们回顾一下上节课的内容，然后进入今天的新知识。"
        "第一部分，我们先来看基本概念和原理，这是后续学习的基础。"
        "接下来，我们通过实际代码演示来加深理解。"
        "请注意这个常见的错误写法，很多初学者都会在这里踩坑。"
        "最后，我们来总结一下本节课的重点内容。"
        "以上就是本节课的全部内容，感谢大家的观看，我们下节课再见。"
    )


async def transcribe_audio(audio_path: str) -> str:
    """Transcribe an audio file to text.

    When ASR_PROVIDER=whisper, uses local openai-whisper model.
    When ASR_PROVIDER=aliyun, uses Aliyun Intelligent Speech Interaction API.
    When ASR_PROVIDER=mock (or the audio file doesn't exist), returns mock transcript.
    Falls back to mock on any API failure.
    """
    # If no real audio file exists (mock pipeline phase), use mock directly
    if not audio_path or not os.path.exists(audio_path):
        return _make_transcript()

    provider = settings.asr_provider

    if provider == "whisper":
        try:
            result = await _whisper_transcribe(audio_path)
            if result:
                return result
        except Exception:
            pass

    if provider == "aliyun":
        try:
            result = await _aliyun_transcribe(audio_path)
            if result:
                return result
        except Exception:
            pass

    # Fallback: mock
    return _make_transcript()


# ---------------------------------------------------------------------------
# Aliyun POP API helpers
# ---------------------------------------------------------------------------

_ALIYUN_ASR_ENDPOINT = "https://filetrans.cn-shanghai.aliyuncs.com"
_ALIYUN_ASR_VERSION = "2018-08-17"


def _percent_encode(s: str) -> str:
    """Percent-encode per Aliyun POP spec: encode / and ~ as well."""
    return urllib.parse.quote(s, safe="").replace("+", "%20").replace("*", "%2A").replace("%7E", "~")


def _pop_sign(http_method: str, params: dict, secret: str) -> str:
    """Compute the Aliyun POP HMAC-SHA1 signature."""
    # Sort params by key
    sorted_items = sorted(params.items(), key=lambda x: x[0])
    canonicalized = "&".join(
        f"{_percent_encode(k)}={_percent_encode(str(v))}" for k, v in sorted_items
    )
    string_to_sign = f"{http_method}&{_percent_encode('/')}&{_percent_encode(canonicalized)}"
    key = secret + "&"
    mac = hmac.new(key.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1)
    return base64.b64encode(mac.digest()).decode("utf-8")


async def _aliyun_transcribe(audio_path: str) -> str | None:
    """Call Aliyun File Transcription API to convert audio to text.

    Requires the audio file to be accessible via a public URL (typically OSS).
    Since we currently have no OSS upload, this will fall back to mock.
    """
    if not all([settings.aliyun_asr_access_key_id, settings.aliyun_asr_access_key_secret, settings.aliyun_asr_app_key]):
        return None

    # In production, you would upload the audio file to OSS first,
    # then pass the OSS URL here. For now, return None to trigger mock fallback.
    audio_url = f"file://{audio_path}"  # Placeholder — needs real OSS URL
    return await _aliyun_submit_and_wait(audio_url)


async def _aliyun_submit_and_wait(audio_url: str, poll_interval: float = 3.0, max_wait: float = 120.0) -> str | None:
    """Submit a file transcription job to Aliyun and poll until complete."""
    # Step 1: Submit the transcription job
    task_id = await _aliyun_submit_task(audio_url)
    if not task_id:
        return None

    # Step 2: Poll for result
    elapsed = 0.0
    while elapsed < max_wait:
        await _async_sleep(poll_interval)
        elapsed += poll_interval
        result = await _aliyun_get_result(task_id)
        if result is None:
            continue
        if result.get("StatusCode") == "FAILED":
            return None
        if result.get("Result"):
            # Extract transcript text from result
            sentences = result.get("Result", {}).get("Sentences", [])
            texts = [s.get("Text", "") for s in sentences if s.get("Text")]
            if texts:
                return "".join(texts)
        return None

    return None


async def _aliyun_submit_task(audio_url: str) -> str | None:
    """Submit a file transcription task to Aliyun. Returns task_id or None."""
    common_params = {
        "Format": "JSON",
        "Version": _ALIYUN_ASR_VERSION,
        "AccessKeyId": settings.aliyun_asr_access_key_id,
        "SignatureMethod": "HMAC-SHA1",
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "SignatureVersion": "1.0",
        "SignatureNonce": str(uuid.uuid4()),
    }
    action_params = {
        "Action": "SubmitFileTransJob",
        "AppKey": settings.aliyun_asr_app_key,
        "FileUrl": audio_url,
        "Region": "cn-shanghai",
    }
    all_params = {**common_params, **action_params}
    all_params["Signature"] = _pop_sign("POST", all_params, settings.aliyun_asr_access_key_secret)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                _ALIYUN_ASR_ENDPOINT,
                data=all_params,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return None

    if data.get("StatusText") == "SUCCESS":
        return data.get("TaskId")
    return None


async def _aliyun_get_result(task_id: str) -> dict | None:
    """Get the result of a file transcription task from Aliyun."""
    common_params = {
        "Format": "JSON",
        "Version": _ALIYUN_ASR_VERSION,
        "AccessKeyId": settings.aliyun_asr_access_key_id,
        "SignatureMethod": "HMAC-SHA1",
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "SignatureVersion": "1.0",
        "SignatureNonce": str(uuid.uuid4()),
    }
    action_params = {
        "Action": "GetFileTransResult",
        "TaskId": task_id,
    }
    all_params = {**common_params, **action_params}
    all_params["Signature"] = _pop_sign("GET", all_params, settings.aliyun_asr_access_key_secret)

    query_string = urllib.parse.urlencode(all_params)
    url = f"{_ALIYUN_ASR_ENDPOINT}?{query_string}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return None


async def _async_sleep(seconds: float):
    import asyncio
    await asyncio.sleep(seconds)


# ---------------------------------------------------------------------------
# Whisper (local) helpers
# ---------------------------------------------------------------------------

_whisper_model = None
_whisper_model_name = None


def _get_whisper_model():
    """Load and cache the Whisper model. Lazy-loads on first call."""
    global _whisper_model, _whisper_model_name
    import whisper

    model_name = settings.asr_whisper_model or "base"
    if _whisper_model is None or _whisper_model_name != model_name:
        _whisper_model = whisper.load_model(model_name)
        _whisper_model_name = model_name
    return _whisper_model


async def _whisper_transcribe(audio_path: str) -> str | None:
    """Transcribe audio using local openai-whisper model (runs in thread executor)."""
    import asyncio

    model = _get_whisper_model()

    def _run():
        result = model.transcribe(audio_path, language="zh", fp16=False)
        return result["text"].strip()

    loop = asyncio.get_event_loop()
    text = await loop.run_in_executor(None, _run)
    return text if text else None
