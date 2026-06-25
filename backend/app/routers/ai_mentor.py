import httpx

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.config import settings
from app.deps import get_current_user
from app.models.user import User
from app.models.ai_chat_record import AIChatRecord
from app.schemas.common import api_response

router = APIRouter()

SYSTEM_PROMPT = """你是一位专业的 Python 编程导师，名叫"启航 AI 助教"。你的职责是：
1. 用中文回答学生的编程问题
2. 解释代码时逐步讲解，先引导思考再给出答案
3. 对于代码纠错需求，先指出问题原因再提供修改建议
4. 使用鼓励性的语气，适合大学本科学生理解
5. 提供实用的代码示例
请始终保持友好、专业、有耐心的态度。不要直接帮学生完成作业，而是引导他们自己思考并理解。"""


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []  # [{role: "user"|"assistant", content: "..."}]


@router.post("/chat")
async def chat_with_mentor(req: ChatRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Send a message to the AI mentor and get a response."""
    if not settings.llm_api_key:
        return api_response(500, "AI 服务未配置，请在环境变量中设置 LLM_API_KEY")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in req.history[-10:]:  # keep last 10 turns
        if h.get("role") in ("user", "assistant"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": req.message})

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.llm_api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
            )
            if resp.status_code != 200:
                return api_response(500, f"AI 服务请求失败: {resp.status_code}")

            data = resp.json()
            reply = data["choices"][0]["message"]["content"]

    except httpx.TimeoutException:
        return api_response(500, "AI 服务响应超时，请稍后再试")
    except Exception as e:
        return api_response(500, f"AI 服务异常: {str(e)}")

    # Save chat record
    db.add(AIChatRecord(
        user_id=user.id,
        question=req.message,
        answer=reply,
        type="ask",
    ))
    await db.commit()

    return api_response(data={
        "reply": reply,
        "model": settings.llm_model,
    })
