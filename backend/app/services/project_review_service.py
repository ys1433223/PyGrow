import json
import logging
import re

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

REVIEW_SYSTEM_PROMPT = """你是一个专业的 Python 编程教师，负责批改学生的综合项目作业。
你需要根据评分量规对学生的项目进行打分和评价。

评分量规（满分100分）：
1. 功能完整性（40分）：项目是否实现了题目要求的所有功能，功能是否正常运行
2. 代码正确性（25分）：代码逻辑是否正确，有无明显bug，边界条件处理
3. 代码规范性（15分）：命名是否规范，有无注释，代码结构是否清晰，PEP8遵循程度
4. 知识点应用（10分）：是否正确运用了题目涉及的知识点，知识点覆盖程度
5. 创新与表达（10分）：是否有自己的思考和创意，代码表达是否清晰易懂

评分等级：
- 90-100：优秀
- 75-89：良好
- 60-74：达标
- 0-59：需修改

你必须返回一个严格的 JSON 格式，不要带任何其他文字：

{
  "total_score": 85,
  "level": "良好",
  "dimension_scores": {
    "功能完整性": 34,
    "代码正确性": 21,
    "代码规范性": 12,
    "知识点应用": 8,
    "创新与表达": 10
  },
  "strengths": ["优点1", "优点2"],
  "problems": ["问题1", "问题2"],
  "suggestions": ["建议1", "建议2"],
  "related_knowledge": ["知识点1", "知识点2"]
}

注意：
- strengths 列出2-3个具体优点，要具体到代码中的细节
- problems 列出2-4个具体问题，要指出问题所在
- suggestions 给出2-4条具体修改建议，要可操作
- related_knowledge 列出2-4个需要复习的知识点
- 评价要客观、鼓励，适合初学者
- 如果是空提交或明显无效提交（完全没有代码或内容），total_score为0，level为"需修改"
"""


def _mock_review(project_title: str, difficulty: str, has_content: bool) -> dict:
    """Return mock review when DeepSeek is unavailable."""
    if not has_content:
        return {
            "total_score": 0,
            "level": "需修改",
            "dimension_scores": {"功能完整性": 0, "代码正确性": 0, "代码规范性": 0, "知识点应用": 0, "创新与表达": 0},
            "strengths": [],
            "problems": ["未提交有效代码或内容，请完成项目后重新提交。"],
            "suggestions": ["按照项目要求编写代码", "完成后检查代码是否能正常运行", "添加必要的注释和文档"],
            "related_knowledge": ["项目相关知识点"],
        }

    base_score = {"easy": 82, "medium": 78, "hard": 72}.get(difficulty, 75)
    return {
        "total_score": base_score,
        "level": "良好" if base_score >= 75 else "达标",
        "dimension_scores": {"功能完整性": int(base_score * 0.4), "代码正确性": int(base_score * 0.25), "代码规范性": int(base_score * 0.15), "知识点应用": int(base_score * 0.1), "创新与表达": max(5, int(base_score * 0.1))},
        "strengths": ["代码结构清晰，逻辑基本正确", "功能实现较为完整"],
        "problems": ["部分边界条件未处理", "代码注释可以更详细"],
        "suggestions": ["添加更完善的错误处理", "补充函数和关键逻辑的注释", "测试更多边界情况"],
        "related_knowledge": ["异常处理", "代码规范", "测试用例设计"],
    }


async def review_project(
    project_title: str,
    task_description: str,
    requirements: list,
    knowledge_tags: list,
    difficulty: str,
    rubric: dict = None,
    code: str = "",
    text: str = "",
    hints_used: int = 0,
) -> dict:
    """Submit project for AI review. Returns structured review result."""
    has_content = bool((code or "").strip() or (text or "").strip())

    if not has_content:
        return _mock_review(project_title, difficulty, False)

    # Build the review prompt
    reqs_text = "\n".join(f"- {r}" for r in (requirements or []))
    tags_text = ", ".join(knowledge_tags or [])
    code_text = (code or "").strip()
    text_content = (text or "").strip()

    student_work = ""
    if code_text:
        student_work += f"## 学生代码\n```python\n{code_text[:3000]}\n```\n\n"
    if text_content:
        student_work += f"## 项目说明\n{text_content[:2000]}\n\n"

    user_prompt = f"""请批改以下学生项目：

## 项目信息
- 项目名称：{project_title}
- 难度：{difficulty}
- 涉及知识点：{tags_text}

## 项目要求
{reqs_text}

## 项目描述
{task_description[:1000]}

{student_work}
请按照评分量规进行打分和评价，返回严格 JSON 格式。"""

    # Try DeepSeek API
    api_key = settings.deepseek_api_key or settings.ai_api_key
    if api_key:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{settings.deepseek_base_url}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.3,
                        "response_format": {"type": "json_object"},
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    # Parse JSON from response
                    result = _parse_review_json(content)
                    if result:
                        logger.info(f"DeepSeek review: {result['total_score']}分 {result['level']}")
                        return result
                    logger.warning("Failed to parse DeepSeek review JSON, using mock")
                else:
                    logger.warning(f"DeepSeek API error {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"DeepSeek API call failed: {e}")

    # Fallback to mock
    logger.info("Using mock review")
    return _mock_review(project_title, difficulty, True)


def _parse_review_json(content: str) -> dict | None:
    """Parse AI response JSON, with fallback extraction."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    # Try to extract JSON block
    m = re.search(r'\{[\s\S]*\}', content)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


def calc_project_xp(
    difficulty: str,
    ai_score: int,
    hints_used: int,
    best_previous_score: int = 0,
) -> dict:
    """Calculate experience gained from project submission."""
    base_xp = {"easy": 40, "medium": 70, "hard": 100}.get(difficulty, 50)

    # AI评分比例
    score_ratio = ai_score / 100.0

    # AI提示系数
    hint_coeff = {0: 1.00, 1: 0.85, 2: 0.70}.get(min(hints_used, 3), 0.55)

    earned = int(base_xp * score_ratio * hint_coeff)

    # 最低经验
    if ai_score > 0 and earned < 10:
        earned = 10
    if ai_score == 0 and earned == 0:
        earned = 0

    # 防刷：只奖励差额
    prev_max = int(best_previous_score / 100 * base_xp * hint_coeff)
    if prev_max > 0:
        diff = earned - prev_max
        earned = max(0, diff)

    return {
        "base_xp": base_xp,
        "score_ratio": round(score_ratio, 2),
        "hint_coefficient": hint_coeff,
        "experience_gained": earned,
        "capped_reason": "历史最高分已获取大部分经验，本次只奖励差额" if prev_max > 0 and earned < int(base_xp * score_ratio * hint_coeff) else None,
    }
