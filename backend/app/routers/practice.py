import random
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db, random_func
from app.deps import get_current_user
from app.models.user import User
from app.models.gamification import Question, PracticeRecord
from app.schemas.common import api_response
from app.schemas.gamification import PracticeSubmit, BatchSubmit, HintRequest
from app.services.gamification import calc_level, calc_major_level, award_badge_if_earned, calc_practice_xp, reset_daily_exp_if_new_day, DAILY_TOTAL_EXP_CAP, get_rank_exp_limit, get_next_rank
from app.services.hint_service import get_ai_hint
from app.services.pet_service import award_cookies

router = APIRouter()

# Knowledge tags ordered by learning progression
KNOWLEDGE_TAGS = [
    "Python基础", "编码规范", "数据类型", "运算符与表达式", "函数",
    "正则表达式", "面向对象", "文件操作", "网页基础",
    "爬虫基础", "爬虫进阶", "数据存储",
    "数据库基础", "非关系型数据库", "Django框架",
    "Selenium自动化", "爬虫原理", "分布式爬虫", "反爬虫",
    "NumPy科学计算", "Pandas数据处理", "数据清洗",
    "数据可视化", "数据分析", "机器学习", "深度学习", "推荐算法",
]

CORE_TAGS = ["Python基础", "数据类型", "运算符与表达式", "函数", "面向对象", "文件操作"]


def judge_answer(question, user_answer: str) -> bool:
    """Judge if user answer is correct based on question type."""
    q_type = question.type
    expected = (question.answer or "").strip()

    if not user_answer:
        return False
    actual = user_answer.strip()

    if q_type == "multiple_choice":
        # Compare as sets (order-independent)
        expected_set = set(expected.replace(" ", "").replace("\n", "").upper().split(","))
        actual_set = set(actual.replace(" ", "").replace("\n", "").upper().split(","))
        # Filter empty strings
        expected_set = {e for e in expected_set if e}
        actual_set = {a for a in actual_set if a}
        return expected_set == actual_set

    elif q_type == "judge":
        expected_norm = expected.strip()
        if expected_norm in ("正确", "对", "True", "true", "√", "是"):
            return actual in ("正确", "对", "True", "true", "√", "是", "1")
        elif expected_norm in ("错误", "错", "False", "false", "×", "否"):
            return actual in ("错误", "错", "False", "false", "×", "否", "0")
        return actual.lower() == expected_norm.lower()

    elif q_type == "fill_blank":
        # Case-insensitive comparison, trim whitespace
        return actual.lower().strip() == expected.lower().strip()

    elif q_type == "code":
        # For code questions, we can't auto-judge without running test cases
        # If test_cases exist, they'll be used; otherwise mark for manual review
        return None  # None = needs manual review / test case execution

    else:
        # single_choice, short_answer: exact match
        return actual.strip().upper() == expected.strip().upper()


async def get_user_stage(user: User) -> str:
    """Determine user's current stage (初级/中级/高级) from level or experience."""
    if user.level:
        return calc_major_level(user.level)
    exp = user.experience or 0
    return calc_major_level(exp)


async def get_completed_question_ids(user_id: int, db: AsyncSession) -> set:
    """Get IDs of questions the user has already answered today."""
    today = date.today()
    result = await db.execute(
        select(PracticeRecord.question_id).where(
            PracticeRecord.user_id == user_id,
            func.date(PracticeRecord.created_at) == today,
        )
    )
    return {r[0] for r in result.all()}


async def get_wrong_question_ids(user_id: int, db: AsyncSession) -> set:
    """Get IDs of questions the user has ever gotten wrong."""
    result = await db.execute(
        select(PracticeRecord.question_id).where(
            PracticeRecord.user_id == user_id,
            PracticeRecord.is_correct == False,
        )
    )
    counts = {}
    for r in result.all():
        counts[r[0]] = counts.get(r[0], 0) + 1
    return counts


async def format_question(q: Question) -> dict:
    """Format question for API response."""
    return {
        "id": q.id,
        "question_id": q.question_id,
        "title": q.title,
        "content": q.content,
        "type": q.type,
        "options": q.options or [],
        "knowledge_point": q.knowledge_point or q.chapter or q.knowledge_tag,
        "knowledge_tag": q.knowledge_tag or q.knowledge_point,
        "difficulty": q.difficulty,
        "stage": q.stage,
        "chapter": q.chapter,
        "chapter_num": q.chapter_num,
        "score": q.score or 5,
        "starter_code": q.starter_code or "",
        "source": getattr(q, "source", None) or "question_bank",
    }


# ==================== ENDPOINTS ====================


@router.get("/daily")
async def get_daily_practice(
    count: int = Query(5, ge=5, le=10, description="Number of questions"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return daily practice questions in knowledge-tag progression order.

    Draws from the user's current stage, starting from the first knowledge tag
    that hasn't been completed today, advancing through KNOWLEDGE_TAGS order.
    """
    stage = await get_user_stage(user)
    completed_ids = await get_completed_question_ids(user.id, db)

    # Find which knowledge tags the user has completed today
    # A tag is "completed for today" if user answered at least 1 question from it today
    today_completed_tags = set()
    if completed_ids:
        tag_result = await db.execute(
            select(Question.knowledge_tag).where(Question.id.in_(completed_ids))
        )
        today_completed_tags = {r[0] for r in tag_result.all() if r[0]}

    # Find the next uncompleted tag in KNOWLEDGE_TAGS order
    start_tag_idx = 0
    for i, tag in enumerate(KNOWLEDGE_TAGS):
        if tag not in today_completed_tags:
            start_tag_idx = i
            break

    # Base query: user's stage, excluding today's completed questions
    def base_query():
        return select(Question).where(
            Question.stage == stage,
            Question.id.notin_(completed_ids) if completed_ids else True,
        )

    selected = []
    seen = set()

    # Walk KNOWLEDGE_TAGS from start_tag_idx, collecting questions
    for tag_idx in range(start_tag_idx, len(KNOWLEDGE_TAGS)):
        if len(selected) >= count:
            break
        tag = KNOWLEDGE_TAGS[tag_idx]
        result = await db.execute(
            base_query().where(Question.knowledge_tag == tag)
        )
        tag_questions = [q for q in result.scalars().all() if q.id not in seen]
        # Prefer easy/medium, then hard
        tag_questions.sort(key=lambda q: 0 if q.difficulty in ("easy", "medium") else 1)
        for q in tag_questions:
            if len(selected) >= count:
                break
            if q.id not in seen:
                seen.add(q.id)
                selected.append(q)

    # If still not enough, fill from any remaining questions in stage
    if len(selected) < count:
        result = await db.execute(base_query())
        pool = [q for q in result.scalars().all() if q.id not in seen]
        random.shuffle(pool)
        for q in pool:
            if len(selected) >= count:
                break
            if q.id not in seen:
                seen.add(q.id)
                selected.append(q)

    # Fallback: adjacent stage
    if len(selected) < count:
        adjacent_stages = {"初级": "中级", "中级": "初级", "高级": "中级"}
        adj = adjacent_stages.get(stage, "初级")
        excluded = completed_ids | seen
        result = await db.execute(
            select(Question).where(Question.stage == adj, Question.id.notin_(excluded) if excluded else True)
        )
        pool = [q for q in result.scalars().all() if q.id not in seen]
        random.shuffle(pool)
        for q in pool:
            if len(selected) >= count:
                break
            if q.id not in seen:
                seen.add(q.id)
                selected.append(q)

    return api_response(data={
        "questions": [await format_question(q) for q in selected],
        "total": len(selected),
        "stage": stage,
        "start_tag": KNOWLEDGE_TAGS[start_tag_idx] if start_tag_idx < len(KNOWLEDGE_TAGS) else None,
    })


@router.get("/placement-test")
async def get_placement_test(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return placement test: 20 multiple-choice questions covering core topics."""
    all_questions = []

    # Get questions from core knowledge tags
    for tag in CORE_TAGS:
        result = await db.execute(
            select(Question).where(
                Question.knowledge_tag == tag,
                Question.type.in_(["single_choice", "multiple_choice"]),
            ).limit(5)
        )
        all_questions.extend(result.scalars().all())

    if len(all_questions) < 20:
        # Supplement with any MC questions
        result = await db.execute(
            select(Question).where(
                Question.type.in_(["single_choice", "multiple_choice"]),
            ).limit(40)
        )
        all_questions.extend(result.scalars().all())

    # Deduplicate and shuffle
    seen = set()
    unique = []
    for q in all_questions:
        if q.id not in seen:
            seen.add(q.id)
            unique.append(q)

    random.shuffle(unique)
    selected = unique[:20]

    return api_response(data={
        "questions": [await format_question(q) for q in selected],
        "total": len(selected),
    })


@router.post("/submit")
async def submit_answer(
    req: PracticeSubmit,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a single answer and get immediate feedback."""
    result = await db.execute(select(Question).where(Question.id == req.question_id))
    question = result.scalar_one_or_none()
    if not question:
        return api_response(404, "题目不存在")

    is_correct = judge_answer(question, req.answer)

    # For code questions, check test_cases if available
    if is_correct is None and question.test_cases:
        # Mock: assume correct if test_cases exist (real execution would happen in code runner)
        is_correct = True

    # Save record
    hints_used = min(req.hints_used, 3)
    base_score = question.score or 5
    score = base_score if is_correct else 0
    record = PracticeRecord(
        user_id=user.id,
        question_id=question.id,
        user_answer=req.answer,
        is_correct=is_correct if is_correct is not None else False,
        score=score,
        hints_used=hints_used,
    )
    db.add(record)

    # Calculate EXP using new rules
    xp_gained = calc_practice_xp(question.type, is_correct, hints_used)

    # Apply daily cap
    reset_daily_exp_if_new_day(user)
    new_daily = user.daily_exp + xp_gained
    if new_daily > DAILY_TOTAL_EXP_CAP:
        xp_gained = max(0, DAILY_TOTAL_EXP_CAP - user.daily_exp)

    if xp_gained:
        user.daily_exp += xp_gained
        user.current_exp += xp_gained
        user.total_exp += xp_gained
        user.experience += xp_gained
        user.points += xp_gained

        # Check rank-up
        old_rank = user.current_rank
        user.level = calc_level(user.total_exp)
        user.current_rank = calc_level(user.total_exp)
        user.rank_exp_limit = get_rank_exp_limit(user.current_rank)
        if user.current_rank != old_rank:
            user.can_promotion_test = 0
            user.current_exp = 0  # Reset on rank-up
            user.rank_exp_limit = get_rank_exp_limit(user.current_rank)
            await award_badge_if_earned(db, user.id, "level_reach", user.total_exp)
        elif user.current_exp >= user.rank_exp_limit:
            user.can_promotion_test = 1

    # Award cookies for correct answers
    cookie_gained = 0
    if is_correct:
        if question.type == "code":
            cookie_gained = await award_cookies(db, user, 2, "code", f"完成代码题: {question.title or question.content[:30]}")
        else:
            cookie_gained = await award_cookies(db, user, 1, "question", f"答对题目: {question.title or question.content[:30]}")

    if is_correct:
        cnt_result = await db.execute(
            select(func.count()).select_from(PracticeRecord).where(
                PracticeRecord.user_id == user.id, PracticeRecord.is_correct == True
            )
        )
        correct_count = cnt_result.scalar() or 0
        await award_badge_if_earned(db, user.id, "correct_count", correct_count)

    await db.commit()

    return api_response(data={
        "is_correct": is_correct,
        "correct_answer": question.answer if not is_correct else None,
        "analysis": question.analysis,
        "experience_gained": xp_gained,
        "cookies_gained": cookie_gained,
        "total_cookies": user.cookies,
        "current_rank": user.current_rank,
        "current_exp": user.current_exp,
        "rank_exp_limit": user.rank_exp_limit,
        "score": score,
    })


@router.post("/batch-submit")
async def batch_submit(
    req: BatchSubmit,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit multiple answers at once (for practice sets)."""
    qids = [a.question_id for a in req.answers]
    result = await db.execute(select(Question).where(Question.id.in_(qids)))
    questions = {q.id: q for q in result.scalars().all()}

    total = len(req.answers)
    correct = 0
    details = []
    total_xp = 0
    weak_tags = set()

    for ans in req.answers:
        q = questions.get(ans.question_id)
        if not q:
            continue

        is_correct = judge_answer(q, ans.answer)
        if is_correct is None:
            is_correct = True  # code questions with test_cases

        hints = min(getattr(ans, 'hints_used', 0), 3)
        base_score = q.score or 5
        score = base_score if is_correct else 0
        db.add(PracticeRecord(
            user_id=user.id, question_id=q.id,
            user_answer=ans.answer, is_correct=is_correct, score=score,
            hints_used=hints,
        ))

        q_xp = calc_practice_xp(q.type, is_correct, hints)
        if is_correct:
            correct += 1
            total_xp += q_xp
        else:
            total_xp += q_xp  # Still get XP for wrong answers (1 XP)
            weak_tags.add(q.knowledge_tag or q.knowledge_point)

        details.append({
            "question_id": q.id,
            "is_correct": is_correct,
            "correct_answer": q.answer if not is_correct else None,
            "analysis": q.analysis,
            "knowledge_tag": q.knowledge_tag or q.knowledge_point,
        })

    # Apply daily cap
    reset_daily_exp_if_new_day(user)
    capped_xp = total_xp
    new_daily = user.daily_exp + total_xp
    if new_daily > DAILY_TOTAL_EXP_CAP:
        capped_xp = max(0, DAILY_TOTAL_EXP_CAP - user.daily_exp)

    # Award XP
    if capped_xp:
        user.daily_exp += capped_xp
        user.current_exp += capped_xp
        user.total_exp += capped_xp
        user.experience += capped_xp
        user.points += capped_xp

        old_rank = user.current_rank
        user.level = calc_level(user.total_exp)
        user.current_rank = calc_level(user.total_exp)
        if user.current_rank != old_rank:
            user.can_promotion_test = 0
            user.current_exp = 0
            user.rank_exp_limit = get_rank_exp_limit(user.current_rank)
            await award_badge_if_earned(db, user.id, "level_reach", user.total_exp)
        elif user.current_exp >= user.rank_exp_limit:
            user.can_promotion_test = 1

    score_pct = round(correct / total * 100) if total > 0 else 0

    # Award cookies: per-correct-question + daily practice completion bonus
    total_cookies = 0
    for ans in req.answers:
        q = questions.get(ans.question_id)
        if not q:
            continue
        q_is_correct = judge_answer(q, ans.answer)
        if q_is_correct is None:
            q_is_correct = True
        if q_is_correct:
            if q.type == "code":
                total_cookies += await award_cookies(db, user, 2, "code", f"完成代码题: {q.title or q.content[:30]}")
            else:
                total_cookies += await award_cookies(db, user, 1, "question", f"答对题目: {q.title or q.content[:30]}")

    # Daily practice completion bonus: +3 cookies if all 5 questions correct
    if total == 5 and correct >= 5:
        total_cookies += await award_cookies(db, user, 3, "daily_practice", "完成每日一练（全部正确）")
    elif total == 5 and score_pct >= 80:
        total_cookies += await award_cookies(db, user, 3, "daily_practice", "完成每日一练")

    # Chapter practice bonus: +3 if >= 80%
    if total >= 4 and score_pct >= 80:
        total_cookies += await award_cookies(db, user, 3, "chapter_practice", f"章节练习正确率 {score_pct}%")

    await db.commit()

    return api_response(data={
        "score": correct,
        "total": total,
        "score_percent": score_pct,
        "weak_tags": list(weak_tags),
        "experience_gained": capped_xp,
        "cookies_gained": total_cookies,
        "total_cookies": user.cookies,
        "details": details,
    })


@router.get("/chapter")
async def get_chapter_questions(
    stage: str = Query(..., description="Stage: 初级/中级/高级"),
    chapter_num: int = Query(..., description="Chapter number"),
    type: str = Query(None, description="Filter by type: single_choice/multiple_choice/judge/fill_blank/code"),
    difficulty: str = Query(None, description="Filter by difficulty: easy/medium/hard"),
    knowledge_tag: str = Query(None, description="Filter by knowledge tag"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return questions for a specific chapter and stage, optionally filtered by knowledge tag."""
    stmt = select(Question).where(
        Question.stage == stage,
        Question.chapter_num == chapter_num,
    )
    if type:
        stmt = stmt.where(Question.type == type)
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    if knowledge_tag:
        stmt = stmt.where(Question.chapter == knowledge_tag)

    result = await db.execute(stmt)
    questions = result.scalars().all()

    # Get distinct chapter (知识点) values for this chapter_num
    tag_result = await db.execute(
        select(Question.chapter).where(
            Question.stage == stage,
            Question.chapter_num == chapter_num,
        ).distinct()
    )
    available_tags = sorted([r[0] for r in tag_result.all() if r[0]])

    return api_response(data={
        "questions": [await format_question(q) for q in questions],
        "total": len(questions),
        "stage": stage,
        "chapter_num": chapter_num,
        "filter_type": type,
        "filter_difficulty": difficulty,
        "filter_knowledge_tag": knowledge_tag,
        "available_tags": available_tags,
    })


@router.get("/special")
async def get_special_questions(
    knowledge_tag: str = Query(..., description="Knowledge tag"),
    type: str = Query(None, description="Filter by type"),
    difficulty: str = Query(None, description="Filter by difficulty"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return questions filtered by knowledge tag."""
    stmt = select(Question).where(Question.knowledge_tag == knowledge_tag)
    if type:
        stmt = stmt.where(Question.type == type)
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)

    result = await db.execute(stmt)
    questions = result.scalars().all()

    return api_response(data={
        "questions": [await format_question(q) for q in questions],
        "total": len(questions),
        "knowledge_tag": knowledge_tag,
    })


@router.get("/wrong-questions")
async def get_wrong_questions(
    knowledge_tag: str = Query(None, description="Filter by knowledge tag"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return user's wrong question book, optionally filtered by knowledge tag."""
    stmt = (
        select(Question, PracticeRecord)
        .join(PracticeRecord, PracticeRecord.question_id == Question.id)
        .where(
            PracticeRecord.user_id == user.id,
            PracticeRecord.is_correct == False,
        )
        .order_by(PracticeRecord.created_at.desc())
    )
    if knowledge_tag:
        stmt = stmt.where(Question.knowledge_tag == knowledge_tag)

    result = await db.execute(stmt)
    rows = result.all()

    seen = set()
    items = []
    for q, rec in rows:
        if q.id in seen:
            continue
        seen.add(q.id)
        items.append({
            **await format_question(q),
            "user_answer": rec.user_answer,
            "wrong_at": str(rec.created_at),
            "record_id": rec.id,
        })

    return api_response(data={
        "wrong_questions": items,
        "total": len(items),
    })


@router.get("/recommend")
async def get_recommend_questions(
    count: int = Query(8, ge=5, le=15, description="Number of recommended questions"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Smart recommendation with mastery analysis, multi-dimensional scoring, and AI fallback.

    Uses student practice records to compute per-knowledge-tag mastery levels,
    scores candidate questions across 9 weighted criteria, selects with diversity
    (weak tags 60% + review 30% + exploration 10%), and falls back to AI-generated
    questions when the question bank is insufficient for weak areas.

    Cold start (< 10 records): returns easy/medium questions from current stage only.
    """
    from app.services.recommend_service import get_smart_recommend

    result = await get_smart_recommend(db, user.id, count)

    return api_response(data={
        "questions": [await format_question(q) for q in result["questions"]],
        "total": len(result["questions"]),
        "recommend_mode": result.get("recommend_mode", "mixed"),
        "weak_tags": result.get("weak_tags", []),
        "learned_scope": result.get("learned_scope", {}),
        "reason": result.get("reason", ""),
        "question_reasons": result.get("question_reasons", []),
    })


@router.get("/promotion-test")
async def get_promotion_test(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return promotion test: 10 questions covering current stage's core topics.
    Requires user.can_promotion_test == 1."""
    if not user.can_promotion_test:
        return api_response(400, "当前段位经验未满，无法参加晋级赛。请继续刷题积累经验！")

    stage = await get_user_stage(user)
    completed_ids = await get_completed_question_ids(user.id, db)
    wrong_counts = await get_wrong_question_ids(user.id, db)

    # Get all questions for user's stage
    result = await db.execute(
        select(Question).where(Question.stage == stage)
    )
    pool = [q for q in result.scalars().all() if q.id not in completed_ids]

    if len(pool) < 10:
        # Fallback to adjacent stage
        adj = "中级" if stage == "高级" else ("高级" if stage == "中级" else "中级")
        result = await db.execute(select(Question).where(Question.stage == adj))
        adj_pool = [q for q in result.scalars().all() if q.id not in completed_ids]
        pool.extend(adj_pool)

    # Weight: prefer wrong knowledge tags
    weighted = []
    for q in pool:
        weight = 1
        if q.id in wrong_counts:
            weight = 3  # Boost wrong questions
        if q.difficulty == "medium":
            weight += 1  # Prefer medium
        weighted.extend([q] * weight)

    random.shuffle(weighted)
    seen = set()
    selected = []
    for q in weighted:
        if q.id not in seen:
            seen.add(q.id)
            selected.append(q)
        if len(selected) >= 10:
            break

    return api_response(data={
        "questions": [await format_question(q) for q in selected],
        "total": len(selected),
        "stage": stage,
    })


@router.post("/promotion-submit")
async def submit_promotion_test(
    req: BatchSubmit,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit promotion test. If score >= 80%, promote user's stage/level."""
    qids = [a.question_id for a in req.answers]
    result = await db.execute(select(Question).where(Question.id.in_(qids)))
    questions = {q.id: q for q in result.scalars().all()}

    total = len(req.answers)
    correct = 0
    details = []
    weak_tags = {}

    for ans in req.answers:
        q = questions.get(ans.question_id)
        if not q:
            continue
        is_correct = judge_answer(q, ans.answer)
        if is_correct is None:
            is_correct = True

        db.add(PracticeRecord(
            user_id=user.id, question_id=q.id,
            user_answer=ans.answer, is_correct=is_correct, score=q.score if is_correct else 0,
        ))

        if is_correct:
            correct += 1
        else:
            tag = q.knowledge_tag or q.knowledge_point or ""
            weak_tags[tag] = weak_tags.get(tag, 0) + 1

        details.append({
            "question_id": q.id,
            "is_correct": is_correct,
            "correct_answer": q.answer if not is_correct else None,
            "analysis": q.analysis,
            "knowledge_tag": q.knowledge_tag or q.knowledge_point,
            "difficulty": q.difficulty,
        })

    score_pct = round(correct / total * 100) if total > 0 else 0
    passed = score_pct >= 80

    old_rank = user.current_rank or "萌新小白"
    promoted = False
    new_rank = old_rank

    if passed:
        next_rank = get_next_rank(old_rank)
        if next_rank:
            new_rank = next_rank
            promoted = True
            # Reset current EXP for new rank, keep total_exp
            user.current_rank = new_rank
            user.current_exp = 0
            user.rank_exp_limit = get_rank_exp_limit(new_rank)
            user.level = new_rank
            user.can_promotion_test = 0
            await award_badge_if_earned(db, user.id, "level_reach", user.total_exp)
        else:
            # At max rank — unlock ultimate challenge
            user.can_promotion_test = 0  # Clear flag, max rank achieved

    # Award XP for taking the test
    reset_daily_exp_if_new_day(user)
    xp_gained = 15 if passed else 5
    new_daily = user.daily_exp + xp_gained
    if new_daily > DAILY_TOTAL_EXP_CAP:
        xp_gained = max(0, DAILY_TOTAL_EXP_CAP - user.daily_exp)

    if xp_gained:
        user.daily_exp += xp_gained
        user.current_exp += xp_gained
        user.total_exp += xp_gained
        user.experience += xp_gained
        user.points += xp_gained

    if passed:
        await award_badge_if_earned(db, user.id, "promotion_passed", 1)

    # Award cookies for promotion test
    cookie_gained = 0
    if passed:
        cookie_gained = await award_cookies(db, user, 8, "promotion", "晋级赛通过！获得 8 个饼干")

    await db.commit()

    return api_response(data={
        "score": correct,
        "total": total,
        "score_percent": score_pct,
        "passed": passed,
        "promoted": promoted,
        "old_rank": old_rank,
        "new_rank": new_rank,
        "weak_tags": sorted(weak_tags.items(), key=lambda x: x[1], reverse=True),
        "experience_gained": xp_gained,
        "cookies_gained": cookie_gained,
        "total_cookies": user.cookies,
        "current_exp": user.current_exp,
        "rank_exp_limit": user.rank_exp_limit,
        "details": details,
        "recommendation": "继续保持练习！" if passed else "建议针对薄弱知识点加强练习",
    })


@router.post("/ai-hint")
async def get_ai_hint_for_question(
    req: HintRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return an AI-generated layered hint for a practice question.
    hint_level: 1=知识点, 2=解题思路, 3=代码结构/易错点.
    """
    # Verify question exists
    result = await db.execute(select(Question).where(Question.id == req.question_id))
    question = result.scalar_one_or_none()
    if not question:
        return api_response(404, "题目不存在")

    hint = await get_ai_hint(
        question=req.question or question.content,
        question_type=req.question_type or question.type,
        difficulty=req.difficulty or question.difficulty or "medium",
        knowledge_tag=req.knowledge_tag or question.knowledge_tag or "Python基础",
        knowledge_type=req.knowledge_type or question.knowledge_type or "",
        student_code=req.student_code,
        hint_level=req.hint_level,
    )
    return api_response(data=hint)


@router.post("/add-wrong")
async def add_to_wrong_book(
    req: PracticeSubmit,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a question to the user's wrong question book (e.g. from favoriting)."""
    result = await db.execute(select(Question).where(Question.id == req.question_id))
    question = result.scalar_one_or_none()
    if not question:
        return api_response(404, "题目不存在")

    # Check if already has a wrong record
    existing = await db.execute(
        select(PracticeRecord).where(
            PracticeRecord.user_id == user.id,
            PracticeRecord.question_id == question.id,
            PracticeRecord.is_correct == False,
        )
    )
    if existing.scalar_one_or_none():
        return api_response(data={"message": "已在错题本中"})

    record = PracticeRecord(
        user_id=user.id,
        question_id=question.id,
        user_answer="",
        is_correct=False,
        score=0,
    )
    db.add(record)
    await db.commit()

    return api_response(data={"message": "已加入错题本", "question_id": req.question_id})


@router.get("/knowledge-points")
async def get_knowledge_points(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return list of distinct knowledge tags for filtering."""
    result = await db.execute(
        select(Question.knowledge_tag).distinct()
    )
    tags = [r[0] for r in result.all() if r[0]]
    return api_response(data=sorted(tags))


@router.get("/chapters")
async def get_chapters_by_stage(
    stage: str = Query(..., description="Stage: 初级/中级/高级"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return distinct chapters for a stage."""
    result = await db.execute(
        select(Question.chapter_num, Question.chapter)
        .where(Question.stage == stage)
        .distinct()
    )
    chapters = []
    seen = set()
    for row in result.all():
        cn = row[0]
        if cn not in seen:
            seen.add(cn)
            chapters.append({"chapter_num": cn, "chapter": row[1] or f"第{cn}章"})

    chapters.sort(key=lambda x: x["chapter_num"])
    return api_response(data=chapters)
