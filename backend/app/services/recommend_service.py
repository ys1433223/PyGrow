import json
import logging
import random
from datetime import date, timedelta
from collections import defaultdict

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.gamification import Question, PracticeRecord
from app.models.user import User
from app.models.course import CourseProgress
from app.services.gamification import calc_major_level

logger = logging.getLogger(__name__)

DEEPSEEK_BASE = "https://api.deepseek.com"

KNOWLEDGE_TAGS = [
    "Python基础", "编码规范", "数据类型", "运算符与表达式", "函数",
    "正则表达式", "面向对象", "文件操作", "网页基础",
    "爬虫基础", "爬虫进阶", "数据存储",
    "数据库基础", "非关系型数据库", "Django框架",
    "Selenium自动化", "爬虫原理", "分布式爬虫", "反爬虫",
    "NumPy科学计算", "Pandas数据处理", "数据清洗",
    "数据可视化", "数据分析", "机器学习", "深度学习", "推荐算法",
]

COLD_START_THRESHOLD = 10
RECENT_DAYS = 30

# ---------- mastery analysis ----------

async def analyze_mastery(db: AsyncSession, user_id: int) -> dict:
    """Return per-knowledge_tag mastery from PracticeRecord joined with Question."""
    result = await db.execute(
        select(PracticeRecord, Question.knowledge_tag)
        .join(Question, PracticeRecord.question_id == Question.id)
        .where(PracticeRecord.user_id == user_id)
        .order_by(PracticeRecord.created_at.desc())
    )
    rows = result.all()
    if not rows:
        return {}

    cutoff = date.today() - timedelta(days=RECENT_DAYS)
    tag_stats = defaultdict(lambda: {
        "total_attempts": 0, "correct_count": 0, "wrong_count": 0,
        "hint_count": 0, "recent_wrong_count": 0, "last_practice_date": None,
        "correct_streak": 0,  # consecutive correct on this tag
    })

    for rec, tag in rows:
        tag = tag or ""
        s = tag_stats[tag]
        s["total_attempts"] += 1
        if rec.is_correct:
            s["correct_count"] += 1
            s["correct_streak"] += 1
        else:
            s["wrong_count"] += 1
            s["correct_streak"] = 0
            if rec.created_at and rec.created_at.date() >= cutoff:
                s["recent_wrong_count"] += 1
        s["hint_count"] += rec.hints_used or 0
        if rec.created_at and (s["last_practice_date"] is None or rec.created_at.date() > s["last_practice_date"]):
            s["last_practice_date"] = rec.created_at.date()

    mastery = {}
    for tag, s in tag_stats.items():
        total = s["total_attempts"]
        accuracy = s["correct_count"] / total if total > 0 else 0.0
        days_since = (date.today() - s["last_practice_date"]).days if s["last_practice_date"] else 999

        if total == 0:
            ml = "untouched"
        elif accuracy < 0.5:
            ml = "weak"
        elif accuracy < 0.7:
            ml = "basic"
        elif accuracy >= 0.85 and (s["recent_wrong_count"] > 0 or days_since > 14):
            ml = "needs_review"
        else:
            ml = "proficient"

        mastery[tag] = {
            "total_attempts": total,
            "correct_count": s["correct_count"],
            "wrong_count": s["wrong_count"],
            "accuracy": round(accuracy, 3),
            "hint_count": s["hint_count"],
            "recent_wrong_count": s["recent_wrong_count"],
            "last_practice_date": str(s["last_practice_date"]) if s["last_practice_date"] else None,
            "days_since_last": days_since,
            "mastery_level": ml,
        }
    return mastery


# ---------- learned scope ----------

async def get_learned_scope(db: AsyncSession, user_id: int) -> dict:
    """Infer learned chapters and tags from CourseProgress and answered questions."""
    # Courses completed or in progress (>30%)
    result = await db.execute(
        select(CourseProgress).where(CourseProgress.user_id == user_id)
    )
    progresses = result.scalars().all()

    learned_chapters = set()
    for cp in progresses:
        if cp.progress_percent and cp.progress_percent >= 30:
            # Map course_id to approximate chapter ranges (from seed data)
            course_chapter_map = {
                1: range(1, 5),   # Python基础 → chapters 1-4
                2: range(5, 9),   # 爬虫 → chapters 5-8
                3: range(9, 13),  # 数据分析 → chapters 9-12
                4: range(13, 16), # ML → chapters 13-15
                5: range(5, 9),   # Django → chapters 5-8
                6: range(9, 13),  # PyTorch → chapters 9-12
            }
            for ch in course_chapter_map.get(cp.course_id, []):
                learned_chapters.add(ch)

    # Also include chapters from answered questions
    tag_result = await db.execute(
        select(Question.chapter_num).join(
            PracticeRecord, PracticeRecord.question_id == Question.id
        ).where(PracticeRecord.user_id == user_id).distinct()
    )
    for r in tag_result.all():
        if r[0]:
            learned_chapters.add(r[0])

    # Known tags
    tag_result2 = await db.execute(
        select(Question.knowledge_tag).join(
            PracticeRecord, PracticeRecord.question_id == Question.id
        ).where(PracticeRecord.user_id == user_id).distinct()
    )
    learned_tags = list({r[0] for r in tag_result2.all() if r[0]})

    total_courses = len([cp for cp in progresses if cp.is_completed])

    return {
        "learned_chapters": sorted(learned_chapters),
        "learned_tags": learned_tags,
        "total_courses_completed": total_courses,
    }


# ---------- scoring ----------

def _tag_rank(tag: str) -> int:
    """Return index of tag in KNOWLEDGE_TAGS, or -1."""
    try:
        return KNOWLEDGE_TAGS.index(tag)
    except ValueError:
        return -1


def _is_adjacent_tag(tag: str, learned_tags: list[str]) -> bool:
    """Check if tag is adjacent (within 2 positions) of any learned tag."""
    idx = _tag_rank(tag)
    if idx < 0:
        return False
    for lt in learned_tags:
        lt_idx = _tag_rank(lt)
        if lt_idx >= 0 and abs(idx - lt_idx) <= 2:
            return True
    return False


def calculate_recommend_score(
    question: Question,
    mastery: dict,
    learned_scope: dict,
    completed_ids: set,
    correct_count_map: dict,
) -> float:
    """Score a candidate question according to weighted criteria. Returns 0-100+."""
    tag = question.knowledge_tag or ""
    tag_m = mastery.get(tag, {})
    ml = tag_m.get("mastery_level", "untouched")
    learned_tags = learned_scope.get("learned_tags", [])
    learned_chapters = set(learned_scope.get("learned_chapters", []))

    score = 0.0

    # 1. Weak mastery tag (+30)
    if ml in ("weak", "basic"):
        score += 30

    # 2. Recent wrong on same tag (+25)
    if tag_m.get("recent_wrong_count", 0) > 0:
        score += 25

    # 3. Not yet attempted this question (+25)
    if question.id not in completed_ids:
        score += 25

    # 4. Within learned chapters (+15)
    if question.chapter_num and question.chapter_num in learned_chapters:
        score += 15

    # 5. Difficulty match (+10)
    if ml in ("weak", "basic"):
        if question.difficulty == "easy":
            score += 10
        elif question.difficulty == "medium":
            score += 5
    else:
        if question.difficulty == "medium":
            score += 10
        elif question.difficulty == "hard":
            score += 5

    # 6. High hint usage on tag (+10)
    if tag_m.get("hint_count", 0) >= 3:
        score += 10

    # 7. Not practiced recently (+8, >14 days)
    if tag_m.get("days_since_last", 0) > 14:
        score += 8

    # 8. Already answered correctly 3+ times (-30)
    if correct_count_map.get(question.id, 0) >= 3:
        score -= 30

    # 9. Outside user's stage, penalty depends on how far
    if question.stage != learned_scope.get("current_stage", ""):
        score -= 50

    return score


# ---------- reason generation ----------

def generate_recommend_reason(question: Question, mastery: dict, learned_scope: dict) -> str:
    tag = question.knowledge_tag or ""
    tag_m = mastery.get(tag, {})
    ml = tag_m.get("mastery_level", "untouched")
    hint_count = tag_m.get("hint_count", 0)
    recent_wrong = tag_m.get("recent_wrong_count", 0)

    if recent_wrong > 0:
        return f"你最近在「{tag}」上错误较多，推荐这道题进行巩固。"
    elif ml == "weak":
        return f"你在「{tag}」知识点上正确率较低，建议加强练习。"
    elif ml == "basic":
        return f"你在「{tag}」上还需巩固，继续加油！"
    elif hint_count >= 3:
        return f"你在「{tag}」知识点上使用 AI 提示较多，建议继续练习。"
    elif ml == "untouched" and tag in learned_scope.get("learned_tags", []):
        return f"「{tag}」是你已学范围内的新知识点，来试试吧。"
    elif ml == "needs_review":
        return f"「{tag}」已经有一段时间没练习了，来复习一下。"
    elif ml == "proficient":
        return f"「{tag}」你已掌握得不错，这道题帮你保持手感。"
    else:
        return "综合巩固练习"


# ---------- AI question generation ----------

AI_GEN_SYSTEM = """你是一个专业的Python编程教学题库生成器。请根据指定的知识点和难度，生成高质量的练习题。

要求：
1. 每道题必须包含：题目文字、题型、选项（选择题需提供）、正确答案、详细解析
2. 题型支持：single_choice（单选）、multiple_choice（多选）、judge（判断）、fill_blank（填空）、code（编程题）
3. 难度分为：easy（简单）、medium（中等）、hard（困难）
4. 答案必须准确无误，解析要详细易懂，适合初学者
5. 返回严格的JSON数组格式，不要包含markdown代码块标记"""

AI_GEN_USER = """请为以下知识点生成{count}道{diff_label}难度的Python练习题：

知识点：{knowledge_tag}
学习阶段：{stage}

请严格按照以下JSON数组格式返回（不要包含```标记）：
[
  {{
    "title": "题目文字内容",
    "type": "single_choice",
    "options": [{{"label": "A", "text": "选项A"}}, {{"label": "B", "text": "选项B"}}, {{"label": "C", "text": "选项C"}}, {{"label": "D", "text": "选项D"}}],
    "answer": "A",
    "analysis": "详细解析说明...",
    "difficulty": "{difficulty}"
  }}
]

注意：
- 如果是judge判断题，options格式为：[{{"label": "A", "text": "正确"}}, {{"label": "B", "text": "错误"}}]
- 如果是fill_blank填空题，options为空数组[]
- 如果是code编程题，options为空数组[]，需要在analysis中说明考察点
- 题目要有实际教学意义，不要出太偏太怪的题"""


async def generate_ai_questions(
    db: AsyncSession,
    knowledge_tag: str,
    stage: str,
    difficulty: str,
    count: int = 2,
) -> list:
    """Call DeepSeek to generate practice questions. Save to DB, return Question instances."""
    api_key = settings.deepseek_api_key or settings.ai_api_key
    if not api_key:
        logger.warning("No AI API key configured, skipping question generation")
        return []

    diff_map = {"easy": "简单", "medium": "中等", "hard": "困难"}
    diff_label = diff_map.get(difficulty, "中等")

    user_prompt = AI_GEN_USER.format(
        count=count,
        diff_label=diff_label,
        knowledge_tag=knowledge_tag,
        stage=stage,
        difficulty=difficulty,
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{DEEPSEEK_BASE}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": AI_GEN_SYSTEM},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.8,
                },
            )
            if resp.status_code != 200:
                logger.warning(f"DeepSeek API error {resp.status_code}: {resp.text[:200]}")
                return []

            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            # Strip markdown fences
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            questions_data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning(f"DeepSeek returned invalid JSON: {e}")
        return []
    except Exception as e:
        logger.warning(f"DeepSeek API call failed: {e}")
        return []

    saved = []
    for qdata in questions_data:
        try:
            q = Question(
                question_id=0,
                title=str(qdata.get("title", ""))[:500],
                content=str(qdata.get("title", ""))[:500],
                type=str(qdata.get("type", "single_choice")),
                options=qdata.get("options", []),
                answer=str(qdata.get("answer", "")),
                analysis=str(qdata.get("analysis", "")),
                knowledge_tag=knowledge_tag,
                knowledge_point=qdata.get("knowledge_point", knowledge_tag),
                difficulty=str(qdata.get("difficulty", difficulty)),
                stage=stage,
                chapter=knowledge_tag,
                chapter_num=0,
                score=qdata.get("score", 5),
                source="ai_generated",
            )
            db.add(q)
            saved.append(q)
        except Exception as e:
            logger.warning(f"Failed to create AI question: {e}")

    if saved:
        await db.flush()
        for q in saved:
            await db.refresh(q)
        logger.info(f"Generated {len(saved)} AI questions for {knowledge_tag}")

    return saved


# ---------- main orchestrator ----------

async def get_smart_recommend(
    db: AsyncSession,
    user_id: int,
    count: int = 8,
) -> dict:
    """Main orchestrator for smart recommendation."""
    # 1. Count total records for cold-start detection
    total_result = await db.execute(
        select(func.count()).select_from(PracticeRecord).where(PracticeRecord.user_id == user_id)
    )
    total_records = total_result.scalar() or 0

    # 2. Mastery analysis
    mastery = await analyze_mastery(db, user_id)

    # 3. Learned scope
    learned_scope = await get_learned_scope(db, user_id)

    # 4. Current stage
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    current_stage = calc_major_level(user.current_rank) if user and user.current_rank else "初级"
    learned_scope["current_stage"] = current_stage

    # 5. All completed question IDs + per-question correct counts
    all_records = await db.execute(
        select(PracticeRecord.question_id, PracticeRecord.is_correct)
        .where(PracticeRecord.user_id == user_id)
    )
    completed_ids = set()
    correct_count_map = defaultdict(int)
    for qid, is_correct in all_records.all():
        completed_ids.add(qid)
        if is_correct:
            correct_count_map[qid] += 1

    # ---- Cold start path ----
    if total_records < COLD_START_THRESHOLD:
        result = await db.execute(
            select(Question).where(
                Question.stage == current_stage,
                Question.difficulty.in_(["easy", "medium"]),
            )
        )
        pool = list(result.scalars().all())
        random.shuffle(pool)
        selected = pool[:count]
        return {
            "questions": selected,
            "total": len(selected),
            "recommend_mode": "foundation_consolidate",
            "weak_tags": [],
            "learned_scope": learned_scope,
            "reason": "你刚起步，系统为你推荐了基础巩固练习题，先打好基础吧！",
            "question_reasons": ["基础巩固推荐" for _ in selected],
        }

    # ---- Full recommendation path ----
    # Get candidate pool: current stage + adjacent
    adjacent_stages = {"初级": "中级", "中级": "初级", "高级": "中级"}
    adj = adjacent_stages.get(current_stage, "初级")

    result = await db.execute(
        select(Question).where(Question.stage.in_([current_stage, adj]))
    )
    candidates = list(result.scalars().all())

    # Score each candidate
    scored = []
    for q in candidates:
        s = calculate_recommend_score(q, mastery, learned_scope, completed_ids, correct_count_map)
        scored.append((s, q))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Select with diversity: top weak tags (60%) + review (30%) + exploration (10%)
    selected = []
    seen_ids = set()

    weak_count = max(1, int(count * 0.6))
    review_count = max(1, int(count * 0.3))
    explore_count = count - weak_count - review_count

    # Tier 1: weak/basic tag questions
    for s, q in scored:
        if len(selected) >= weak_count:
            break
        tag_m = mastery.get(q.knowledge_tag or "", {})
        if tag_m.get("mastery_level") in ("weak", "basic") and q.id not in seen_ids:
            seen_ids.add(q.id)
            selected.append(q)

    # Tier 2: needs_review / recent wrong
    for s, q in scored:
        if len(selected) >= weak_count + review_count:
            break
        tag_m = mastery.get(q.knowledge_tag or "", {})
        if tag_m.get("mastery_level") == "needs_review" and q.id not in seen_ids:
            seen_ids.add(q.id)
            selected.append(q)

    # Tier 3: exploration (untouched but in learned scope)
    for s, q in scored:
        if len(selected) >= count:
            break
        if q.id not in seen_ids:
            seen_ids.add(q.id)
            selected.append(q)

    # Fill remaining from top scored
    for s, q in scored:
        if len(selected) >= count:
            break
        if q.id not in seen_ids:
            seen_ids.add(q.id)
            selected.append(q)

    # ---- AI fallback ----
    ai_generated = []
    if len(selected) < count:
        shortfall = count - len(selected)
        # Find top weak tags
        weak_tags_sorted = sorted(
            [(tag, m) for tag, m in mastery.items() if m["mastery_level"] in ("weak", "basic")],
            key=lambda x: x[1]["accuracy"],
        )[:3]
        for tag, _ in weak_tags_sorted:
            if shortfall <= 0:
                break
            # Count existing AI-generated for this tag
            ai_existing = await db.execute(
                select(func.count()).select_from(Question).where(
                    Question.knowledge_tag == tag,
                    Question.source == "ai_generated",
                    Question.id.notin_(completed_ids),
                )
            )
            existing_count = ai_existing.scalar() or 0
            needed = min(shortfall, 3 - existing_count)
            if needed > 0:
                gen_qs = await generate_ai_questions(db, tag, current_stage, "easy", needed)
                for gq in gen_qs:
                    if shortfall <= 0:
                        break
                    ai_generated.append(gq)
                    selected.append(gq)
                    shortfall -= 1

    # ---- Random fallback if still short ----
    if len(selected) < count:
        remaining = await db.execute(
            select(Question).where(
                Question.stage == current_stage,
                Question.id.notin_({q.id for q in selected}),
            )
        )
        fill_pool = list(remaining.scalars().all())
        random.shuffle(fill_pool)
        for q in fill_pool:
            if len(selected) >= count:
                break
            selected.append(q)

    # Build per-question reasons
    question_reasons = []
    for q in selected[:count]:
        if q in ai_generated:
            question_reasons.append(f"题库中相关题已完成，系统为你生成了一道「{q.knowledge_tag}」新题。")
        else:
            question_reasons.append(generate_recommend_reason(q, mastery, learned_scope))

    selected = selected[:count]

    # Determine recommend_mode
    weak_count_in_selected = sum(
        1 for q in selected if mastery.get(q.knowledge_tag or "", {}).get("mastery_level") in ("weak", "basic")
    )
    if ai_generated:
        mode = "ai_supplement"
    elif weak_count_in_selected >= len(selected) * 0.5:
        mode = "weakness_reinforce"
    elif any(mastery.get(q.knowledge_tag or "", {}).get("recent_wrong_count", 0) > 0 for q in selected):
        mode = "wrong_review"
    else:
        mode = "mixed"

    # Weak tags (top 5, accuracy < 0.5, sorted by accuracy)
    weak_tags = sorted(
        [(tag, m["accuracy"]) for tag, m in mastery.items() if m["accuracy"] < 0.5 and m["total_attempts"] > 0],
        key=lambda x: x[1],
    )[:5]

    return {
        "questions": selected,
        "total": len(selected),
        "recommend_mode": mode,
        "weak_tags": weak_tags,
        "learned_scope": learned_scope,
        "reason": _mode_reason(mode, weak_tags),
        "question_reasons": question_reasons,
    }


def _mode_reason(mode: str, weak_tags: list) -> str:
    if mode == "foundation_consolidate":
        return "基础巩固推荐：从当前阶段选取适合你水平的题目，稳步提升。"
    elif mode == "weakness_reinforce":
        tags = ", ".join(t for t, _ in weak_tags[:3])
        return f"薄弱补强：针对你正确率较低的「{tags}」等知识点进行强化训练。"
    elif mode == "wrong_review":
        return "错题复习：针对你近期做错的知识点进行巩固练习。"
    elif mode == "ai_supplement":
        return "AI补充练习：题库中相关题已完成，AI为你生成了新的练习题。"
    else:
        return "混合推荐：综合你的学习情况，推荐最适合的练习题。"
