from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.project import ProjectSubmission
from app.models.gamification import UserDailyTask
from app.schemas.common import api_response
from app.services.gamification import MAJOR_LEVELS

router = APIRouter()


def _get_levels_for_major(major_level: str = None) -> list[str] | None:
    """If major_level is given, return the sub-levels; otherwise None meaning no filter."""
    if not major_level or major_level not in MAJOR_LEVELS:
        return None
    return MAJOR_LEVELS[major_level]


def _apply_level_filter(q, model, major_level: str):
    """Apply level filter to a query if major_level is specified."""
    sub_levels = _get_levels_for_major(major_level)
    if sub_levels:
        return q.where(model.level.in_(sub_levels))
    return q


@router.get("/xp")
async def leaderboard_xp(
    major_level: str = None,
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rank users by total experience, optionally filtered by major level."""
    q = select(User.id, User.username, User.avatar, User.level, User.experience, User.points)
    q = _apply_level_filter(q, User, major_level)
    q = q.order_by(desc(User.experience)).limit(limit)

    result = await db.execute(q)
    rows = result.all()

    items = []
    for i, r in enumerate(rows):
        items.append({
            "rank": i + 1,
            "user_id": r[0], "username": r[1], "avatar": r[2],
            "level": r[3], "experience": r[4], "points": r[5],
        })

    my_rank = None
    for item in items:
        if item["user_id"] == user.id:
            my_rank = item
            break

    return api_response(data={"leaderboard": items, "my_rank": my_rank})


@router.get("/projects")
async def leaderboard_projects(
    major_level: str = None,
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rank users by number of project submissions, optionally filtered by major level."""
    q = select(
        ProjectSubmission.user_id,
        func.count(ProjectSubmission.id).label("project_count"),
        User.username, User.avatar, User.level
    ).join(User, ProjectSubmission.user_id == User.id)
    q = _apply_level_filter(q, User, major_level)
    q = q.group_by(ProjectSubmission.user_id).order_by(desc("project_count")).limit(limit)

    rows = (await db.execute(q)).all()

    items = []
    for i, r in enumerate(rows):
        items.append({
            "rank": i + 1, "user_id": r[0],
            "username": r[2] or "未知", "avatar": r[3] or "",
            "level": r[4] or "", "project_count": r[1],
        })

    my_count_result = await db.execute(
        select(func.count(ProjectSubmission.id)).where(ProjectSubmission.user_id == user.id)
    )
    my_count = my_count_result.scalar() or 0

    return api_response(data={"leaderboard": items, "my_project_count": my_count})


@router.get("/streak")
async def leaderboard_streak(
    major_level: str = None,
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rank users by active days in last 30 days, optionally filtered by major level."""
    import datetime
    today = datetime.date.today()

    q = select(
        UserDailyTask.user_id,
        func.count(func.distinct(UserDailyTask.date)).label("active_days"),
        User.username, User.avatar, User.level
    ).join(User, UserDailyTask.user_id == User.id)
    q = q.where(UserDailyTask.date >= today - datetime.timedelta(days=30))
    q = _apply_level_filter(q, User, major_level)
    q = q.group_by(UserDailyTask.user_id).order_by(desc("active_days")).limit(limit)

    rows = (await db.execute(q)).all()

    items = []
    for i, r in enumerate(rows):
        items.append({
            "rank": i + 1, "user_id": r[0],
            "username": r[2] or "未知", "avatar": r[3] or "",
            "level": r[4] or "", "active_days": r[1],
        })

    return api_response(data={"leaderboard": items})
