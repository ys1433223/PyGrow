from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db, random_func
from app.deps import get_current_user
from app.models.user import User
from app.models.course import Course, CourseProgress
from app.models.gamification import Question, PracticeRecord, UserDailyTask, DailyTask, UserBadge
from app.schemas.common import api_response
from app.schemas.gamification import AssessmentSubmit
from app.services.gamification import calc_level, calc_level_progress, award_badge_if_earned

router = APIRouter()


@router.get("/questions")
async def get_assessment_questions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Return 20 random questions for assessment."""
    result = await db.execute(
        select(Question).order_by(random_func()).limit(20)
    )
    questions = result.scalars().all()
    return api_response(data=[
        {
            "id": q.id,
            "title": q.title,
            "content": q.content,
            "type": q.type,
            "options": q.options or [],
            "knowledge_point": q.knowledge_point,
            "difficulty": q.difficulty,
        }
        for q in questions
    ])


@router.post("/submit")
async def submit_assessment(
    req: AssessmentSubmit,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Grade assessment and return result with level + recommendations."""
    question_ids = [int(k) for k in req.answers.keys()]
    result = await db.execute(select(Question).where(Question.id.in_(question_ids)))
    questions = {q.id: q for q in result.scalars().all()}

    total = len(questions)
    correct = 0
    weak_points = set()
    wrong_questions = []

    for qid, user_answer in req.answers.items():
        q = questions.get(qid)
        if not q:
            continue
        expected = q.answer.strip().lower() if q.answer else ""
        actual = user_answer.strip().lower() if isinstance(user_answer, str) else str(user_answer).strip().lower()

        # For multi-select, answers are comma-separated
        if q.type == "multi":
            expected_set = set(expected.replace(" ", "").split(","))
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

        db.add(PracticeRecord(user_id=user.id, question_id=qid, user_answer=str(user_answer), is_correct=is_correct, score=5 if is_correct else 0))

    score_pct = round(correct / total * 100) if total > 0 else 0

    # Determine level
    if score_pct <= 40:
        assess_level = "入门级"
    elif score_pct <= 60:
        assess_level = "初级"
    elif score_pct <= 80:
        assess_level = "中级"
    else:
        assess_level = "高级"

    # Award XP
    user.experience += 20
    user.points += 20
    old_level = user.level
    user.level = calc_level(user.experience)

    # Check badges
    earned_badges = await award_badge_if_earned(db, user.id, "assessment_complete", 1)
    if score_pct == 100:
        more = await award_badge_if_earned(db, user.id, "assessment_perfect", 1)
        earned_badges.extend(more)
    if old_level != user.level:
        more = await award_badge_if_earned(db, user.id, "level_reach", user.experience)
        earned_badges.extend(more)

    # Recommend courses
    result = await db.execute(select(Course).limit(3))
    recommended = [
        {"id": c.id, "title": c.title, "category": c.category, "cover_color": c.cover_color}
        for c in result.scalars().all()
    ]

    await db.commit()

    return api_response(data={
        "score": correct,
        "total": total,
        "score_percent": score_pct,
        "level": assess_level,
        "weak_points": list(weak_points),
        "wrong_questions": wrong_questions,
        "recommended_courses": recommended,
        "experience_gained": 20,
        "new_level": user.level,
        "new_badges": earned_badges,
    })


@router.get("/result")
async def get_assessment_result(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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
