import os
import shutil
import subprocess
import logging

logger = logging.getLogger(__name__)


def find_ffmpeg() -> str | None:
    """Return the path to ffmpeg, or None if not installed."""
    return shutil.which("ffmpeg")


def extract_audio(video_path: str, output_audio_path: str) -> str:
    """Extract audio from a video file using FFmpeg.

    Output format: WAV, 16kHz, mono, 16-bit PCM — optimized for ASR.

    Args:
        video_path: Path to the input video file (e.g., .mp4).
        output_audio_path: Desired output audio path (e.g., .wav).

    Returns:
        The output_audio_path on success.

    Raises:
        RuntimeError: If FFmpeg is not installed, the video file doesn't exist,
                      or FFmpeg exits with a non-zero code.
    """
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("当前环境未安装 FFmpeg，请先安装 FFmpeg")

    if not os.path.exists(video_path):
        raise RuntimeError(f"视频文件不存在: {video_path}")

    # Ensure output directory exists
    out_dir = os.path.dirname(output_audio_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    cmd = [
        ffmpeg,
        "-y",                          # overwrite output
        "-i", video_path,
        "-vn",                          # skip video stream
        "-acodec", "pcm_s16le",         # 16-bit PCM
        "-ar", "16000",                 # 16 kHz sample rate
        "-ac", "1",                     # mono
        output_audio_path,
    ]

    logger.info("Running FFmpeg: %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown error"
        logger.error("FFmpeg failed: %s", stderr)
        raise RuntimeError(f"FFmpeg 音频提取失败: {stderr[-500:]}")

    if not os.path.exists(output_audio_path) or os.path.getsize(output_audio_path) == 0:
        raise RuntimeError("FFmpeg 完成但未生成有效音频文件")

    logger.info("Audio extracted: %s", output_audio_path)
    return output_audio_path
