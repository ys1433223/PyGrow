import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

DEEPSEEK_BASE = "https://api.deepseek.com"

# ---------------------------------------------------------------------------
# Knowledge type → hint modes (3 levels each)
# ---------------------------------------------------------------------------
KNOWLEDGE_TYPE_MODES = {
    "concept": [
        {"mode": "concept_card", "title": "概念卡片"},
        {"mode": "example", "title": "举个例子"},
        {"mode": "keyword", "title": "记忆关键词"},
    ],
    "comparison": [
        {"mode": "compare_table", "title": "对比表"},
        {"mode": "judge_basis", "title": "判断依据"},
        {"mode": "confusion_point", "title": "常见混淆点"},
    ],
    "application": [
        {"mode": "key_info", "title": "关键信息"},
        {"mode": "approach", "title": "解题思路"},
        {"mode": "pitfall", "title": "易错提醒"},
    ],
    "code": [
        {"mode": "knowledge_point", "title": "相关知识点"},
        {"mode": "approach", "title": "解题思路"},
        {"mode": "code_structure", "title": "代码结构"},
    ],
    "debug": [
        {"mode": "error_meaning", "title": "报错含义"},
        {"mode": "locate", "title": "定位方向"},
        {"mode": "fix_idea", "title": "修改思路"},
    ],
}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "你是一个耐心的Python教学助手，帮助初学者学习编程。"
    "你必须严格遵守以下规则："
    "1. 绝对不允许直接给出正确答案或正确选项。"
    "2. 绝对不允许直接填写填空题的答案。"
    "3. 绝对不允许给出完整的可运行代码。"
    "4. 对于概念题，可以直接解释相关概念。"
    "5. 对于代码题，可以给代码骨架，但关键部分用...或注释代替。"
    "6. 用鼓励的语气，帮助学生自己思考。"
    "7. 回答限制在200字以内。"
)

# ---------------------------------------------------------------------------
# Per-mode prompts
# ---------------------------------------------------------------------------
MODE_PROMPTS = {
    # ---- concept ----------------------------------------------------------
    "concept_card": (
        "学生正在学习「{knowledge_tag}」相关的概念。\n题目：{question}\n\n"
        "请解释这道题涉及的核心概念（如相关的Python语法、函数、数据结构等）。"
        "直接解释概念本身，不要涉及解题方法。用简洁的语言，像教学卡片一样。200字以内。"
    ),
    "example": (
        "学生正在学习「{knowledge_tag}」。\n题目：{question}\n\n"
        "请给一个与这道题知识点相关的简单代码例子，用通俗易懂的方式帮助学生理解概念的实际用法。"
        "例子要和题目相关但不要直接给出题目答案。150字以内。"
    ),
    "keyword": (
        "学生正在学习「{knowledge_tag}」。\n题目：{question}\n\n"
        "请列出这道题涉及的3-5个关键记忆词汇或短语，帮助学生快速回顾重点。"
        "每行一个关键词加简短解释。不要给出答案。150字以内。"
    ),

    # ---- comparison -------------------------------------------------------
    "compare_table": (
        "学生正在学习「{knowledge_tag}」相关的易混概念。\n题目：{question}\n\n"
        "请用对比的方式列出这道题涉及的易混概念之间的核心差异。"
        "可以用【概念A vs 概念B：...】的格式。不要直接告诉答案，只帮助区分概念。200字以内。"
    ),
    "judge_basis": (
        "学生正在学习「{knowledge_tag}」。\n题目：{question}\n学生目前的回答：{student_code}\n\n"
        "请提示判断这道题应该用什么方法和依据（如：看到什么特征应该想到哪个概念）。"
        "不要直接给答案。150字以内。"
    ),
    "confusion_point": (
        "学生正在学习「{knowledge_tag}」。\n题目：{question}\n\n"
        "请指出这道题涉及的常见混淆点——学生最容易在哪里犯糊涂、把什么和什么搞混。"
        "直接点出混淆点，帮助学生避免踩坑。150字以内。"
    ),

    # ---- application ------------------------------------------------------
    "key_info": (
        "学生在做一道关于「{knowledge_tag}」的应用理解题。\n题目：{question}\n\n"
        "请帮助学生提取题目中的关键信息：题目给了什么条件、要求什么结果。"
        "只梳理信息，不给解题步骤。150字以内。"
    ),
    "approach": (
        "学生正在做一道关于「{knowledge_tag}」的应用理解题。\n题目：{question}\n学生目前的回答：{student_code}\n\n"
        "请给出解题思路和方法提示（如应该按什么步骤思考、用什么方法）。"
        "不要给具体答案或正确选项。180字以内。"
    ),
    "pitfall": (
        "学生正在做一道关于「{knowledge_tag}」的应用理解题。\n题目：{question}\n\n"
        "请提示这道题的易错点和常见误区（如容易忽略的细节、典型的错误理解）。"
        "不要直接给答案。150字以内。"
    ),

    # ---- code -------------------------------------------------------------
    "code_knowledge_point": (
        "学生正在做一道关于「{knowledge_tag}」的代码题。\n题目：{question}\n\n"
        "请提示这道编程题涉及的知识点（如需要用到的Python函数、数据结构、语法等）。"
        "只列出相关知识点，不给解题步骤或代码。150字以内。"
    ),
    "code_approach": (
        "学生正在做一道关于「{knowledge_tag}」的代码题。\n题目：{question}\n学生目前的代码：{student_code}\n\n"
        "请给出解题思路和步骤提示（先做什么、再做什么、用什么方法）。"
        "不要写具体代码。180字以内。"
    ),
    "code_structure": (
        "学生正在做一道关于「{knowledge_tag}」的代码题。\n题目：{question}\n学生目前的代码：{student_code}\n\n"
        "请给出代码骨架提示（函数框架、关键步骤作为注释）。"
        "不要给出完整可运行的代码！关键逻辑用注释或...代替。200字以内。"
    ),

    # ---- debug ------------------------------------------------------------
    "error_meaning": (
        "学生遇到了一个Python报错。\n题目/报错信息：{question}\n\n"
        "请解释这个报错信息的含义：这个错误类型代表什么、通常在什么情况下出现。"
        "用简单易懂的语言解释，适合初学者理解。150字以内。"
    ),
    "locate": (
        "学生在调试一道Python题。\n题目/报错信息：{question}\n学生目前的代码：{student_code}\n\n"
        "请提示排查方向：应该从哪些方面入手检查代码（如检查哪一行、检查什么类型的错误）。"
        "不要直接指出具体错误位置。150字以内。"
    ),
    "fix_idea": (
        "学生在调试一道Python题。\n题目/报错信息：{question}\n学生目前的代码：{student_code}\n\n"
        "请提示修改思路和方法（如可能需要用什么方式解决、常见的修复方法）。"
        "不要给完整修复后的代码，只给方向性建议。180字以内。"
    ),

    # ---- remediation (level 4 / "still don't understand") -----------------
    "remediation": (
        "学生连续查看了多个提示仍然不理解一道关于「{knowledge_tag}」的题目。"
        "\n题目：{question}\n\n"
        "请生成一个简短的知识点补救卡片，包含以下内容：\n"
        "1. 【核心概念】用一句话解释核心概念\n"
        "2. 【简单例子】给一个最简单的代码例子\n"
        "3. 【易错点】列出最常见的1-2个错误\n"
        "4. 【记忆关键词】3-5个关键词\n"
        "用友好的语气鼓励学生。不要直接给出本道题的答案！总计250字以内。"
    ),
}


def _infer_knowledge_type(question_type: str, knowledge_tag: str, question: str) -> str:
    """Infer knowledge_type when not explicitly set in DB."""
    if question_type == "code":
        return "code"

    q_lower = (knowledge_tag + " " + question).lower()

    debug_keywords = ["traceback", "报错", "调试", "错误", "debug", "exception", "异常"]
    if any(kw in q_lower for kw in debug_keywords):
        return "debug"

    comp_keywords = ["区别", "对比", "异同", "比较", "vs", "不同于", "相同点"]
    if any(kw in q_lower for kw in comp_keywords):
        return "comparison"

    concept_keywords = ["概念", "定义", "是什么", "含义", "基本", "基础概念"]
    if any(kw in q_lower for kw in concept_keywords) or question_type in ("judge", "fill_blank"):
        return "concept"

    return "application"


def _get_mode_config(knowledge_type: str, hint_level: int) -> dict:
    """Get the mode config for a given knowledge_type and hint_level.
    hint_level 1-3 maps to the 3 modes; 4 = remediation."""
    if hint_level == 4:
        return {"mode": "remediation", "title": "知识点补救卡片"}

    modes = KNOWLEDGE_TYPE_MODES.get(knowledge_type, KNOWLEDGE_TYPE_MODES["application"])
    if hint_level < 1 or hint_level > 3:
        hint_level = 1
    return modes[hint_level - 1]


def _build_user_prompt(
    mode: str,
    knowledge_type: str,
    knowledge_tag: str,
    question: str,
    student_code: str,
) -> str:
    """Build the user prompt for the given mode."""
    # code type uses "code_knowledge_point" / "code_approach" / "code_structure"
    prompt_key = mode
    if knowledge_type == "code" and mode in ("knowledge_point", "approach", "code_structure"):
        prompt_key = "code_" + mode

    template = MODE_PROMPTS.get(prompt_key, MODE_PROMPTS["approach"])
    return template.format(
        knowledge_tag=knowledge_tag or "Python基础",
        question=question,
        student_code=student_code or "（学生还没有作答）",
    )


# ---------------------------------------------------------------------------
# Mock fallback hints
# ---------------------------------------------------------------------------
_MOCK_CONTENT = {
    ("concept", 1): (
        "核心概念解释：这道题考察「{tag}」相关的Python基础知识。"
        "建议回顾一下这个概念的准确定义和基本用法。把概念理解清楚了，题目就迎刃而解啦！"
    ),
    ("concept", 2): (
        "举个简单例子：\n"
        "```python\n"
        "# 假设我们使用{tag}来处理数据\n"
        "result = some_function(input_value)  # 这里的关键是理解参数和返回值\n"
        "```\n"
        "对照这个模式，想想你的题目中数据是怎么流转的？"
    ),
    ("concept", 3): (
        "记忆关键词：\n"
        "1. {tag} — 核心考点，回忆它的定义\n"
        "2. 参数类型 — 输入需要什么格式\n"
        "3. 返回值 — 输出是什么\n"
        "4. 边界条件 — 特殊情况怎么处理\n"
        "记住这些关键点，对照题目逐个检查！"
    ),
    ("comparison", 1): (
        "对比要点：\n"
        "• 相似点 — 两个概念看起来哪里像？\n"
        "• 不同点 — 核心区别在什么地方？\n"
        "• 使用场景 — 各自适用于什么情况？\n"
        "把这三个维度想清楚，答案就明朗了。"
    ),
    ("comparison", 2): (
        "判断依据：先看题目描述中出现了哪些关键词，这些关键词通常关联到哪个概念。"
        "然后注意题目要求的条件（如数据类型、操作方式），不同类型的条件对应不同的选择。"
        "逐条对比，逐个排除。"
    ),
    ("comparison", 3): (
        "常见混淆点：很多同学在这里容易把{tag}的用法和其他相似概念搞混。"
        "特别注意：名字相近不代表功能相同，同一个方法在不同上下文里的行为可能完全不同。"
        "再仔细读一遍题，注意每个选项的措辞差异。"
    ),
    ("application", 1): (
        "关键信息提取：\n"
        "• 题目给了什么条件？\n"
        "• 要求什么结果？\n"
        "先把这两个问题回答清楚，然后想想{tag}中的哪些知识能帮到你。"
    ),
    ("application", 2): (
        "解题思路：\n"
        "1. 仔细审题，明确输入和输出\n"
        "2. 回顾{tag}的相关知识点\n"
        "3. 用排除法先去掉明显不对的\n"
        "4. 在剩下的选项中仔细推理\n"
        "不要急着下结论，多思考一下每个选项为什么对为什么错。"
    ),
    ("application", 3): (
        "易错提醒：\n"
        "• 注意审题——有没有看漏的条件？\n"
        "• 概念混淆——{tag}和其他知识点的区别清楚吗？\n"
        "• 细节陷阱——缩进、大小写、标点这些都看了吗？\n"
        "做对题目往往就差在细节上，再仔细检查一遍！"
    ),
    ("code", 1): (
        "相关知识点：这道题需要用到{tag}相关的Python技能。"
        "建议回顾一下：需要什么数据结构？用什么内置函数？循环还是判断？把这些基础工具盘点清楚再动手写代码。"
    ),
    ("code", 2): (
        "解题思路：\n"
        "1. 先想清楚输入是什么，输出要什么\n"
        "2. 中间需要什么数据处理步骤\n"
        "3. 每一步用到{tag}的哪个方法或语法\n"
        "在纸上画出数据流图，然后一步步翻译成代码。"
    ),
    ("code", 3): (
        "代码骨架提示：\n"
        "```python\n"
        "# 1. 定义函数，明确参数\n"
        "def solve(input_data):\n"
        "    # 2. 初始化结果变量\n"
        "    # 3. 用{tag}相关方法处理数据\n"
        "    # 4. 返回结果\n"
        "    pass  # 想想每一行应该写什么\n"
        "```\n"
        "框架有了，关键是填对每个步骤的具体逻辑。"
    ),
    ("debug", 1): (
        "报错含义：这个错误通常意味着Python在执行时遇到了不符合预期的情况。"
        "先看报错信息的第一行（错误类型）和最后一行（具体位置），它们会告诉你大概是什么问题。"
        "理解了报错信息的字面意思，就成功了一半。"
    ),
    ("debug", 2): (
        "定位方向：\n"
        "1. 先看报错指向的行号\n"
        "2. 检查该行及前一行的代码\n"
        "3. 确认变量值是否符合预期\n"
        "4. 检查缩进和语法\n"
        "从报错位置前后3行开始排查，通常问题就藏在那里。"
    ),
    ("debug", 3): (
        "修改思路：\n"
        "• 先确认错误类型对应的常见解决方案\n"
        "• 检查数据类型是否匹配\n"
        "• 确认循环/判断条件是否正确\n"
        "• 必要时用print调试中间值\n"
        "不要害怕报错，每一次调试都是成长的机会！"
    ),
}


def _mock_remediation(knowledge_tag: str) -> dict:
    return {
        "hint_level": 4,
        "hint_mode": "remediation",
        "title": "知识点补救卡片",
        "content": f"【核心概念】\n{knowledge_tag}是Python编程中的重要知识点，理解它的基本原理和常见用法是解决此类题目的关键。\n\n"
                   f"【简单例子】\n涉及{knowledge_tag}的基本用法可以参考Python官方文档或教材中的第一个示例，从最简单的场景开始理解。\n\n"
                   f"【易错点】\n1. 容易和其他相似概念混淆\n2. 特殊边界条件容易被忽略\n\n"
                   f"【记忆关键词】\n{knowledge_tag}、基本用法、参数类型、返回值、边界条件",
        "examples": "",
        "common_mistakes": "概念混淆、忽略边界条件",
        "keywords": f"{knowledge_tag}, 基本用法, 参数类型, 边界条件",
        "still_no_answer": True,
    }


def _mock_hint(knowledge_type: str, knowledge_tag: str, hint_level: int) -> dict:
    """Return mock hints when DeepSeek API is unavailable."""
    modes = KNOWLEDGE_TYPE_MODES.get(knowledge_type, KNOWLEDGE_TYPE_MODES["application"])

    if hint_level == 4:
        return _mock_remediation(knowledge_tag)

    if hint_level < 1 or hint_level > 3:
        hint_level = 1

    mode_info = modes[hint_level - 1]
    content = _MOCK_CONTENT.get((knowledge_type, hint_level), _MOCK_CONTENT[("application", hint_level)])
    # Replace {tag} with actual tag
    if "{tag}" in content:
        content = content.replace("{tag}", knowledge_tag or "这个知识点")

    return {
        "hint_level": hint_level,
        "hint_mode": mode_info["mode"],
        "title": mode_info["title"],
        "content": content,
        "examples": "",
        "common_mistakes": "",
        "keywords": "",
        "still_no_answer": False,
    }


# ---------------------------------------------------------------------------
# Main hint function
# ---------------------------------------------------------------------------
async def get_ai_hint(
    question: str,
    question_type: str,
    difficulty: str,
    knowledge_tag: str,
    student_code: str = "",
    hint_level: int = 1,
    knowledge_type: str = "",
) -> dict:
    """Get AI-generated hint for a question.

    Returns:
        {hint_level, hint_mode, title, content, examples, common_mistakes,
         keywords, still_no_answer}
    """
    # Infer knowledge_type if not provided
    if not knowledge_type:
        knowledge_type = _infer_knowledge_type(question_type, knowledge_tag, question)

    # Get mode config
    mode_info = _get_mode_config(knowledge_type, hint_level)
    mode = mode_info["mode"]

    # Build the user prompt
    user_prompt = _build_user_prompt(
        mode, knowledge_type, knowledge_tag, question, student_code,
    )

    # Try DeepSeek API
    api_key = settings.deepseek_api_key or settings.ai_api_key
    content = None

    if api_key:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{DEEPSEEK_BASE}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        "max_tokens": 400,
                        "temperature": 0.7,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    logger.info(f"DeepSeek hint {knowledge_type} L{hint_level} ({mode}): {len(content)} chars")
                else:
                    logger.warning(f"DeepSeek API error {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"DeepSeek API call failed: {e}")

    # Build result
    result = {
        "hint_level": hint_level,
        "hint_mode": mode,
        "title": mode_info["title"],
        "content": content or "",
        "examples": "",
        "common_mistakes": "",
        "keywords": "",
        "still_no_answer": hint_level == 4,
    }

    # If DeepSeek returned content, use it; otherwise fall back to mock
    if content:
        return result

    # Fallback to mock
    logger.info(f"Using mock hint for {knowledge_type} level {hint_level}")
    return _mock_hint(knowledge_type, knowledge_tag, hint_level)
