import random

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.course import Course, CourseProgress
from app.models.gamification import Question, PracticeRecord, UserDailyTask, DailyTask, UserBadge
from app.schemas.common import api_response
from app.schemas.gamification import AssessmentSubmit
from app.services.gamification import (
    calc_rank, get_rank_exp_limit, award_badge_if_earned, RANK_TIERS,
)

router = APIRouter()

PLACEMENT_QUESTION_COUNT = 10
POINTS_PER_QUESTION = 10

# Score% → initial rank mapping (first match from top)
PLACEMENT_RANK_MAP = [
    (70, "稳扎玩家"),
    (60, "达标选手"),
    (45, "勤学学徒"),
    (30, "萌新小白"),
]
DEFAULT_RANK = "萌新小白"

# Core topics for placement test with gradient difficulty
PLACEMENT_TOPICS = [
    # (tag, count, difficulty preference)
    ("Python基础", 2, "easy"),
    ("编码规范", 1, "easy"),
    ("数据类型", 2, "easy"),
    ("运算符与表达式", 1, "medium"),
    ("函数", 2, "medium"),
    ("面向对象", 1, "medium"),
    ("文件操作", 1, "medium"),
]


@router.get("/questions")
async def get_assessment_questions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a structured 20-question placement test (100 points total).

    Questions cover core Python topics with a basic→intermediate gradient,
    drawn from stage 初级/中级, difficulty easy/medium.
    """
    selected = []
    seen_ids = set()
    topics_fallback = list(PLACEMENT_TOPICS)

    for tag, target_count, preferred_diff in topics_fallback:
        # Try preferred difficulty first
        result = await db.execute(
            select(Question).where(
                Question.knowledge_tag == tag,
                Question.difficulty == preferred_diff,
                Question.type.in_(["single_choice", "multiple_choice"]),
            ).order_by(func.rand()).limit(target_count)
        )
        batch = [q for q in result.scalars().all() if q.id not in seen_ids]

        # If not enough, supplement with any difficulty from same tag
        if len(batch) < target_count:
            remaining = target_count - len(batch)
            result = await db.execute(
                select(Question).where(
                    Question.knowledge_tag == tag,
                    Question.type.in_(["single_choice", "multiple_choice"]),
                ).order_by(func.rand()).limit(remaining * 2)
            )
            for q in result.scalars().all():
                if q.id not in seen_ids and len(batch) < target_count:
                    batch.append(q)

        for q in batch:
            if q.id not in seen_ids:
                seen_ids.add(q.id)
                selected.append(q)

    # Fill remaining slots with any MC questions from 初级/中级
    if len(selected) < PLACEMENT_QUESTION_COUNT:
        shortage = PLACEMENT_QUESTION_COUNT - len(selected)
        result = await db.execute(
            select(Question).where(
                Question.type.in_(["single_choice", "multiple_choice"]),
                Question.stage.in_(["初级", "中级"]),
            ).order_by(func.rand()).limit(shortage * 3)
        )
        for q in result.scalars().all():
            if q.id not in seen_ids and len(selected) < PLACEMENT_QUESTION_COUNT:
                seen_ids.add(q.id)
                selected.append(q)

    # Still not enough — grab anything
    if len(selected) < PLACEMENT_QUESTION_COUNT:
        shortage = PLACEMENT_QUESTION_COUNT - len(selected)
        result = await db.execute(
            select(Question).where(
                Question.type.in_(["single_choice", "multiple_choice"]),
            ).order_by(func.rand()).limit(shortage * 3)
        )
        for q in result.scalars().all():
            if q.id not in seen_ids and len(selected) < PLACEMENT_QUESTION_COUNT:
                seen_ids.add(q.id)
                selected.append(q)

    random.shuffle(selected)
    selected = selected[:PLACEMENT_QUESTION_COUNT]

    return api_response(data=[
        {
            "id": q.id,
            "title": q.title,
            "content": q.content,
            "type": q.type,
            "options": q.options or [],
            "knowledge_point": q.knowledge_point,
            "difficulty": q.difficulty,
            "score": POINTS_PER_QUESTION,
        }
        for q in selected
    ])


@router.post("/submit")
async def submit_assessment(
    req: AssessmentSubmit,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Grade placement test and assign initial rank based on score percentage.

    Rank mapping:
      - 30%~44% → 萌新小白
      - 45%~59% → 勤学学徒
      - 60%~69% → 达标选手
      - 70%+    → 稳扎玩家
      - < 30%   → 萌新小白 (default)
    """
    question_ids = [int(k) for k in req.answers.keys()]
    result = await db.execute(select(Question).where(Question.id.in_(question_ids)))
    questions = {q.id: q for q in result.scalars().all()}

    total = len(questions)
    correct = 0
    weak_points = set()
    wrong_questions = []

    for qid, user_answer in req.answers.items():
        q = questions.get(int(qid))
        if not q:
            continue
        expected = q.answer.strip().lower() if q.answer else ""
        actual = user_answer.strip().lower() if isinstance(user_answer, str) else str(user_answer).strip().lower()

        if q.type == "multiple_choice" or q.type == "multi":
            # DB answers are concatenated letters like "ABD"; frontend sends comma-separated like "A,B,D"
            if "," in expected:
                expected_set = set(expected.split(","))
            else:
                expected_set = set(expected)
            actual_set = set(actual.replace(" ", "").split(","))
            is_correct = expected_set == actual_set
        else:
            is_correct = actual == expected

        if is_correct:
            correct += 1
        else:
            weak_points.add(q.knowledge_point)
            wrong_questions.append({
                "id": q.id, "title": q.title, "content": q.content,
                "type": q.type, "options": q.options or [],
                "user_answer": user_answer, "correct_answer": q.answer,
                "analysis": q.analysis, "knowledge_point": q.knowledge_point,
            })

        db.add(PracticeRecord(
            user_id=user.id, question_id=qid,
            user_answer=str(user_answer),
            is_correct=is_correct,
            score=POINTS_PER_QUESTION if is_correct else 0,
        ))

    score_pct = round(correct / total * 100) if total > 0 else 0

    # Determine initial rank from score %
    new_rank = DEFAULT_RANK
    for threshold, rank_name in PLACEMENT_RANK_MAP:
        if score_pct >= threshold:
            new_rank = rank_name
            break

    # Award XP proportional to score (bonus for placement)
    xp_gained = 50 + correct * 3  # base 50 + 3 per correct question
    rank_exp_limit = get_rank_exp_limit(new_rank)

    # Update new rank system fields
    user.current_rank = new_rank
    user.current_exp = 0  # start fresh in the new rank
    user.rank_exp_limit = rank_exp_limit
    user.total_exp = (user.total_exp or 0) + xp_gained
    user.can_promotion_test = 0  # must earn EXP to unlock promotion

    # Also sync legacy fields
    user.level = new_rank
    user.experience = (user.experience or 0) + xp_gained
    user.points = (user.points or 0) + xp_gained

    # Check badges
    earned_badges = await award_badge_if_earned(db, user.id, "assessment_complete", 1)
    if score_pct == 100:
        more = await award_badge_if_earned(db, user.id, "assessment_perfect", 1)
        earned_badges.extend(more)

    # Recommend courses
    result = await db.execute(select(Course).limit(3))
    recommended = [
        {"id": c.id, "title": c.title, "category": c.category, "cover_color": c.cover_color}
        for c in result.scalars().all()
    ]

    await db.commit()

    # Find rank index for display
    rank_idx = -1
    for i, (name, _) in enumerate(RANK_TIERS):
        if name == new_rank:
            rank_idx = i
            break

    return api_response(data={
        "score": correct,
        "total": total,
        "score_percent": score_pct,
        "assigned_rank": new_rank,
        "rank_index": rank_idx,
        "rank_exp_limit": rank_exp_limit,
        "weak_points": list(weak_points),
        "wrong_questions": wrong_questions,
        "recommended_courses": recommended,
        "experience_gained": xp_gained,
        "new_badges": earned_badges,
    })


@router.get("/result")
async def get_assessment_result(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return most recent assessment score record."""
    result = await db.execute(
        select(PracticeRecord)
        .where(PracticeRecord.user_id == user.id)
        .order_by(PracticeRecord.created_at.desc())
        .limit(20)
    )
    records = result.scalars().all()
    if not records:
        return api_response(404, "暂无测评记录")

    total = len(records)
    correct = sum(1 for r in records if r.is_correct)
    score_pct = round(correct / total * 100) if total > 0 else 0

    return api_response(data={
        "score": correct,
        "total": total,
        "score_percent": score_pct,
        "level": user.level,
    })
