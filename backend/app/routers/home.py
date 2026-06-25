from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.course import Course, CourseProgress
from app.models.gamification import DailyTask, UserDailyTask, UserBadge, Badge, PracticeRecord
from app.schemas.common import api_response
from app.services.gamification import calc_rank_progress, get_consecutive_days, award_badge_if_earned, reset_daily_exp_if_new_day, DAILY_TOTAL_EXP_CAP

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Homepage dashboard data."""
    today = date.today()

    # Rank info (new system)
    reset_daily_exp_if_new_day(user)
    rank_info = calc_rank_progress(user.current_rank or "萌新小白", user.current_exp or 0, user.total_exp or 0)

    # Daily tasks
    all_tasks = (await db.execute(select(DailyTask))).scalars().all()
    ut_result = await db.execute(
        select(UserDailyTask).where(UserDailyTask.user_id == user.id, UserDailyTask.date == today)
    )
    user_tasks = {ut.task_id: ut for ut in ut_result.scalars().all()}

    tasks = []
    for t in all_tasks:
        ut = user_tasks.get(t.id)
        tasks.append({
            "id": t.id, "title": t.title, "description": t.description,
            "task_type": t.task_type, "reward_exp": t.reward_exp, "reward_points": t.reward_points,
            "is_completed": ut.is_completed if ut else False,
        })

    # Continue learning: most recently progressed course
    progress_result = await db.execute(
        select(CourseProgress).where(CourseProgress.user_id == user.id, CourseProgress.is_completed == False)
        .order_by(CourseProgress.updated_at.desc()).limit(1)
    )
    recent = progress_result.scalar_one_or_none()
    continue_learning = None
    if recent:
        c = (await db.execute(select(Course).where(Course.id == recent.course_id))).scalar_one_or_none()
        if c:
            continue_learning = {
                "course_id": c.id, "title": c.title,
                "progress_percent": recent.progress_percent or 0,
                "cover_color": c.cover_color,
            }

    # Recommended courses (courses not started or in progress)
    result = await db.execute(select(Course).limit(4))
    all_courses = result.scalars().all()
    recommended = [
        {"id": c.id, "title": c.title, "category": c.category, "cover_color": c.cover_color, "description": c.description}
        for c in all_courses
    ]

    # Check if user has completed assessment
    assess_result = await db.execute(select(PracticeRecord).where(PracticeRecord.user_id == user.id).limit(1))
    has_assessment = assess_result.scalar_one_or_none() is not None

    # Update last_login and check streak
    if user.last_login_at is None:
        user.last_login_at = func.now()
        await db.commit()
    else:
        await db.commit()

    streak = await get_consecutive_days(db, user.id)
    await award_badge_if_earned(db, user.id, "streak_days", streak)

    return api_response(data={
        "current_rank": rank_info["current_rank"],
        "major_level": rank_info["major_level"],
        "current_exp": rank_info["current_exp"],
        "rank_exp_limit": rank_info["rank_exp_limit"],
        "total_exp": rank_info["total_exp"],
        "progress_percent": rank_info["progress_percent"],
        "next_rank": rank_info["next_rank"],
        "can_promotion_test": rank_info["can_promotion_test"],
        "daily_exp": user.daily_exp or 0,
        "daily_exp_cap": DAILY_TOTAL_EXP_CAP,
        "cookies": user.cookies or 0,
        "points": user.points,
        "streak_days": streak,
        "daily_tasks": tasks,
        "continue_learning": continue_learning,
        "recommended_courses": recommended,
        "has_assessment": has_assessment,
    })
