from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.gamification import Badge, UserBadge, DailyTask, UserDailyTask
from app.schemas.common import api_response
from app.schemas.gamification import ClaimReward
from app.services.gamification import calc_level, calc_major_level, calc_rank_progress, award_badge_if_earned, get_consecutive_days, reset_daily_exp_if_new_day, DAILY_TOTAL_EXP_CAP, DAILY_TASK_EXP_CAP, get_rank_exp_limit
from app.services.pet_service import award_cookies

router = APIRouter()


@router.get("/status")
async def get_gamification_status(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Return user's rank, EXP, cookies, badges with new rank system."""
    reset_daily_exp_if_new_day(user)
    rank_info = calc_rank_progress(user.current_rank or "萌新小白", user.current_exp or 0, user.total_exp or 0)

    result = await db.execute(
        select(Badge).join(UserBadge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.user_id == user.id)
    )
    badges = [{"id": b.id, "name": b.name, "description": b.description, "icon_url": b.icon_url} for b in result.scalars().all()]

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
        "daily_cookies": user.daily_cookies or 0,
        "daily_cookie_cap": 30,
        "points": user.points,
        "badges": badges,
    })


@router.get("/daily-tasks")
async def get_daily_tasks(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Return today's tasks with completion status and ensure entries exist."""
    today = date.today()

    all_tasks = (await db.execute(select(DailyTask))).scalars().all()

    result = await db.execute(
        select(UserDailyTask).where(UserDailyTask.user_id == user.id, UserDailyTask.date == today)
    )
    user_tasks = {ut.task_id: ut for ut in result.scalars().all()}

    items = []
    for t in all_tasks:
        ut = user_tasks.get(t.id)
        items.append({
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "task_type": t.task_type,
            "reward_exp": t.reward_exp,
            "reward_points": t.reward_points,
            "is_completed": ut.is_completed if ut else False,
        })

    return api_response(data=items)


@router.post("/claim-reward")
async def claim_task_reward(
    req: ClaimReward,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark task complete and award XP."""
    today = date.today()

    task = (await db.execute(select(DailyTask).where(DailyTask.id == req.task_id))).scalar_one_or_none()
    if not task:
        return api_response(404, "任务不存在")

    existing = (await db.execute(
        select(UserDailyTask).where(UserDailyTask.user_id == user.id, UserDailyTask.task_id == req.task_id, UserDailyTask.date == today)
    )).scalar_one_or_none()

    if existing and existing.is_completed:
        return api_response(400, "今日已领取")

    if not existing:
        existing = UserDailyTask(user_id=user.id, task_id=req.task_id, date=today)
        db.add(existing)

    existing.is_completed = True
    existing.completed_at = func.now()

    # Apply daily cap
    reset_daily_exp_if_new_day(user)
    xp_to_add = task.reward_exp
    new_daily = user.daily_exp + xp_to_add
    if new_daily > DAILY_TOTAL_EXP_CAP:
        xp_to_add = max(0, DAILY_TOTAL_EXP_CAP - user.daily_exp)

    if xp_to_add:
        user.daily_exp += xp_to_add
        user.current_exp += xp_to_add
        user.total_exp += xp_to_add
        user.experience += xp_to_add
    user.points += task.reward_points

    # Update rank
    old_rank = user.current_rank
    user.level = calc_level(user.total_exp)
    user.current_rank = calc_level(user.total_exp)
    if user.current_rank != old_rank:
        user.can_promotion_test = 0
        user.current_exp = 0
        user.rank_exp_limit = get_rank_exp_limit(user.current_rank)
    elif user.current_exp >= user.rank_exp_limit:
        user.can_promotion_test = 1

    earned = []
    if old_rank != user.current_rank:
        earned = await award_badge_if_earned(db, user.id, "level_reach", user.total_exp)
    await award_badge_if_earned(db, user.id, "points_total", user.points)

    # Update last_login_at for streak tracking
    if user.last_login_at is None:
        user.last_login_at = func.now()

    # Award cookies for daily tasks
    cookie_gained = await award_cookies(db, user, 1, "daily_task", f"完成每日任务: {task.title}")

    # Check if all daily tasks are completed -> bonus +5 cookies
    all_tasks = (await db.execute(select(DailyTask))).scalars().all()
    user_tasks_result = await db.execute(
        select(UserDailyTask).where(UserDailyTask.user_id == user.id, UserDailyTask.date == today)
    )
    user_tasks = {ut.task_id: ut for ut in user_tasks_result.scalars().all()}
    all_completed = all(len(user_tasks) == len(all_tasks) and all(
        user_tasks.get(t.id) and (user_tasks[t.id].is_completed or t.id == req.task_id)
        for t in all_tasks
    ))
    if all_completed and len(all_tasks) > 0:
        # Check we haven't already awarded the bonus
        from app.models.pet import PetCookieRecord
        bonus_exists = await db.execute(
            select(PetCookieRecord).where(
                PetCookieRecord.user_id == user.id,
                PetCookieRecord.source_type == "daily_task_all",
                func.date(PetCookieRecord.created_at) == today,
            )
        )
        if not bonus_exists.scalar_one_or_none():
            cookie_gained += await award_cookies(db, user, 5, "daily_task_all", "今日任务全部完成！获得 5 个饼干")

    # Sign-in streak: +5 cookies for 3 consecutive days
    streak = await get_consecutive_days(db, user.id)
    if streak >= 3:
        from app.models.pet import PetCookieRecord
        streak_record_exists = await db.execute(
            select(PetCookieRecord).where(
                PetCookieRecord.user_id == user.id,
                PetCookieRecord.source_type == "signin",
                func.date(PetCookieRecord.created_at) == today,
            )
        )
        if not streak_record_exists.scalar_one_or_none():
            cookie_gained += await award_cookies(db, user, 5, "signin", f"连续签到 {streak} 天！获得 5 个饼干")

    await db.commit()

    return api_response(data={
        "experience_gained": xp_to_add,
        "points_gained": task.reward_points,
        "cookies_gained": cookie_gained,
        "total_cookies": user.cookies,
        "current_rank": user.current_rank,
        "current_exp": user.current_exp,
        "rank_exp_limit": user.rank_exp_limit,
        "total_exp": user.total_exp,
        "new_badges": earned,
    })
