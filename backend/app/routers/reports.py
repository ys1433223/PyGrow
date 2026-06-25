from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.course import CourseProgress
from app.models.gamification import PracticeRecord, Question
from app.schemas.common import api_response
from app.services.gamification import calc_level_progress

router = APIRouter()


@router.get("/summary")
async def get_report_summary(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Learning report summary."""
    # Course count
    course_result = await db.execute(
        select(CourseProgress).where(CourseProgress.user_id == user.id)
    )
    progress_list = course_result.scalars().all()
    completed_courses = sum(1 for p in progress_list if p.is_completed)
    in_progress = len(progress_list) - completed_courses

    # Practice stats
    total_result = await db.execute(
        select(func.count()).select_from(PracticeRecord).where(PracticeRecord.user_id == user.id)
    )
    total_practice = total_result.scalar() or 0

    correct_result = await db.execute(
        select(func.count()).select_from(PracticeRecord).where(
            PracticeRecord.user_id == user.id, PracticeRecord.is_correct == True
        )
    )
    correct_count = correct_result.scalar() or 0
    wrong_count = total_practice - correct_count
    accuracy = round(correct_count / total_practice * 100) if total_practice > 0 else 0

    lvl_info = calc_level_progress(user.experience)

    return api_response(data={
        "completed_courses": completed_courses,
        "in_progress_courses": in_progress,
        "total_practice": total_practice,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "accuracy": accuracy,
        "level": lvl_info["current_level"],
        "experience": user.experience,
        "points": user.points,
    })


@router.get("/knowledge-points")
async def get_knowledge_report(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Knowledge point mastery data for chart display."""
    result = await db.execute(
        select(
            Question.knowledge_point,
            func.count().label("total"),
            func.sum(PracticeRecord.is_correct).label("correct"),
        )
        .join(PracticeRecord, PracticeRecord.question_id == Question.id)
        .where(PracticeRecord.user_id == user.id)
        .group_by(Question.knowledge_point)
    )
    rows = result.all()

    knowledge = []
    for kp, total, correct in rows:
        pct = round(correct / total * 100) if total else 0
        knowledge.append({
            "knowledge_point": kp,
            "total": total,
            "correct": correct or 0,
            "mastery_percent": pct,
        })

    return api_response(data=knowledge)
