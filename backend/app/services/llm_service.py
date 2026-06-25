import json
import httpx

from app.config import settings


def make_mock_note_data(course_title: str) -> dict:
    """Generate mock AI notes (fallback when LLM is unavailable)."""
    return {
        "summary": f"本节课主要讲解{ course_title }的核心知识点，涵盖基本概念、常用操作和实际应用场景。",
        "notes": [
            f"理解{ course_title }的基本概念和核心原理。",
            "掌握常用函数和操作方法。",
            "了解实际开发中的最佳实践。",
            "能够独立完成相关练习题。",
        ],
        "highlights": [
            {"time": "00:30", "title": "课程导入"},
            {"time": "02:15", "title": "核心概念讲解"},
            {"time": "04:40", "title": "实操演示"},
            {"time": "08:10", "title": "知识点总结"},
        ],
        "transcript": f"大家好，本节课我们来学习{ course_title }。首先来看基本概念……（此处为模拟文稿）……以上就是本节课的全部内容，感谢观看！",
        "errors": [
            "注意区分大小写，Python 对大小写敏感。",
            "函数调用时不要忘记加括号。",
            "缩进错误是最常见的语法问题。",
        ],
        "suggestions": [
            "建议先完成本节课的章节练习巩固基础。",
            "可以尝试修改示例代码观察不同结果。",
            "学习后进入每日一练加强记忆。",
            "遇到问题可以在讨论区发帖交流。",
        ],
    }

SYSTEM_PROMPT = """你是一位专业的 Python 编程教学助手。请根据提供的课程标题和视频文稿，生成一份结构化的学习笔记。

要求：
1. summary：用一句话概括本节课的核心内容（不超过80字）
2. notes：列出 6-10 条具体详细的知识点，每条应包含：
   - 具体的语法规则、函数名、参数说明或代码示例
   - 操作步骤的关键细节和注意事项
   - 不要写概括性描述，要写"XX函数用于...，其参数X表示...，返回值是..."
   - 每条应让学习者看完就能直接运用
3. highlights：列出 4 个视频关键时间节点，每个节点配一个简短标题
   - 时间格式 mm:ss
   - 第1个时间节点从 00:30 开始
   - 后续节点均匀分布到视频总时长（用户会提供具体时长）
   - 时间节点不能超出视频总时长
4. errors：列出 3-4 条初学者常见易错点
5. suggestions：给出 3-4 条具体的学习建议

请严格按照以下 JSON 格式返回，不要包含 markdown 代码块标记：
{
  "summary": "...",
  "notes": ["...", "..."],
  "highlights": [{"time": "00:30", "title": "..."}, ...],
  "errors": ["...", "..."],
  "suggestions": ["...", "..."]
}"""


async def generate_ai_notes(course_title: str, transcript: str, video_duration_sec: float = 0.0) -> dict:
    """Call the LLM to generate structured AI notes. Falls back to mock data on failure."""
    if not settings.ai_api_key:
        return make_mock_note_data(course_title)

    # Build duration hint for the timestamp prompt
    duration_hint = ""
    if video_duration_sec > 0:
        minutes = int(video_duration_sec // 60)
        seconds = int(video_duration_sec % 60)
        duration_hint = f"\n视频总时长：{minutes}分{seconds}秒（约{int(video_duration_sec)}秒）。请确保所有时间节点不超出此范围。"

    url = f"{settings.ai_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.ai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.ai_model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"课程标题：{course_title}{duration_hint}\n\n视频文稿：\n{transcript}"},
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

            content = data["choices"][0]["message"]["content"]
            # Strip possible markdown code fences
            content = content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                # Remove first line (```json) and last line (```)
                content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            result = json.loads(content)

            # Validate required fields
            required = ["summary", "notes", "highlights", "errors", "suggestions"]
            for field in required:
                if field not in result:
                    result[field] = make_mock_note_data(course_title)[field]

            # Validate timestamps don't exceed video duration
            if video_duration_sec > 0 and "highlights" in result:
                for h in result["highlights"]:
                    try:
                        parts = h["time"].split(":")
                        ts_sec = int(parts[0]) * 60 + int(parts[1])
                        if ts_sec > video_duration_sec + 5:  # Allow 5s tolerance
                            h["time"] = f"{int(video_duration_sec // 60):02d}:{int(video_duration_sec % 60):02d}"
                    except (ValueError, IndexError):
                        pass

            result.setdefault("transcript", transcript)
            return result

    except Exception:
        return make_mock_note_data(course_title)
