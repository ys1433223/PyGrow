import datetime
from app.models.gamification import Badge, UserBadge, DailyTask, UserDailyTask

# ========== 8 Ranks with EXP caps ==========
# Each rank has an EXP cap. When current_exp reaches the cap, promotion test unlocks.
RANK_TIERS = [
    ("萌新小白", 100),
    ("勤学学徒", 200),
    ("达标选手", 350),
    ("稳扎玩家", 550),
    ("进阶干将", 800),
    ("学科达人", 1100),
    ("专业先锋", 1500),
    ("满级学神", 2000),
]

MAJOR_LEVELS = {
    "初级": ["萌新小白", "勤学学徒", "达标选手"],
    "中级": ["稳扎玩家", "进阶干将", "学科达人"],
    "高级": ["专业先锋", "满级学神"],
}

# ========== Daily EXP Caps ==========
DAILY_TASK_EXP_CAP = 50      # Max EXP from daily tasks
DAILY_PRACTICE_EXP_CAP = 80   # Max EXP from practice questions
DAILY_TOTAL_EXP_CAP = 140     # Suggested total daily cap

# ========== Practice EXP Rules ==========
# 普通题 (non-code)
NORMAL_XP = {
    "correct_no_hint": 8,
    "correct_1_hint": 6,
    "correct_2_hint": 4,
    "correct_3_hint": 2,
    "wrong": 1,
}
# 代码题 (code)
CODE_XP = {
    "pass_no_hint": 15,
    "pass_1_hint": 12,
    "pass_2_hint": 8,
    "pass_3_hint": 5,
    "valid_no_pass": 2,
}

# ========== Project Cookie Rewards ==========
PROJECT_COOKIE_REWARDS = {
    "excellent": 10,  # 90-100
    "good": 5,        # 75-89
    "fail": 0,        # <60
}


def get_rank_index(rank_name: str) -> int:
    """Get index of a rank in RANK_TIERS, -1 if not found."""
    for i, (name, _) in enumerate(RANK_TIERS):
        if name == rank_name:
            return i
    return -1


def get_rank_exp_limit(rank_name: str) -> int:
    """Get EXP cap for a rank."""
    for name, cap in RANK_TIERS:
        if name == rank_name:
            return cap
    return 100


def get_next_rank(current_rank: str) -> str | None:
    """Get the next rank name, None if at max."""
    idx = get_rank_index(current_rank)
    if idx < 0 or idx >= len(RANK_TIERS) - 1:
        return None
    return RANK_TIERS[idx + 1][0]


def calc_rank(total_exp: int) -> str:
    """Derive rank from total_exp (for backward compat / initialization)."""
    cumulative = 0
    for name, cap in RANK_TIERS:
        cumulative += cap
        if total_exp < cumulative:
            return name
    return RANK_TIERS[-1][0]


def calc_rank_progress(current_rank: str, current_exp: int, total_exp: int) -> dict:
    """Return structured rank progress info."""
    limit = get_rank_exp_limit(current_rank)
    idx = get_rank_index(current_rank)
    pct = min(100, round(current_exp / limit * 100)) if limit > 0 else 100
    major = calc_major_level(current_rank)
    next_rank = get_next_rank(current_rank)
    return {
        "current_rank": current_rank,
        "major_level": major,
        "current_exp": current_exp,
        "rank_exp_limit": limit,
        "progress_percent": pct,
        "total_exp": total_exp,
        "next_rank": next_rank,
        "can_promotion_test": current_exp >= limit and next_rank is not None,
    }


def calc_practice_xp(question_type: str, is_correct: bool, hints_used: int) -> int:
    """Calculate EXP earned for a single practice question."""
    hints = min(hints_used, 3)
    is_code = (question_type == "code")

    if is_code:
        if is_correct:
            key = f"pass_{hints}_hint" if hints > 0 else "pass_no_hint"
            return CODE_XP.get(key, 5)
        else:
            return CODE_XP["valid_no_pass"]
    else:
        if is_correct:
            key = f"correct_{hints}_hint" if hints > 0 else "correct_no_hint"
            return NORMAL_XP.get(key, 8)
        else:
            return NORMAL_XP["wrong"]


# Legacy compat
LEVEL_TIERS = [(name, 0, cap) for name, cap in RANK_TIERS]


def calc_level(experience: int) -> str:
    """Legacy: derive level name from total XP."""
    return calc_rank(experience)


def calc_major_level(experience_or_sub_level: str | int) -> str:
    """Return major level (初级/中级/高级) from XP or rank name."""
    if isinstance(experience_or_sub_level, int):
        sub = calc_rank(experience_or_sub_level)
    else:
        sub = experience_or_sub_level
    for major, subs in MAJOR_LEVELS.items():
        if sub in subs:
            return major
    return "初级"


def calc_level_progress(experience: int) -> dict:
    """Legacy progress from total_exp. Adapts to new rank system."""
    rank = calc_rank(experience)
    # Estimate current_exp within this rank by subtracting cumulative caps
    cumulative = 0
    for name, cap in RANK_TIERS:
        if name == rank:
            current = experience - cumulative
            limit = cap
            break
        cumulative += cap
    else:
        current = experience
        limit = 2000

    info = calc_rank_progress(rank, current, experience)
    return {
        "current_level": info["current_rank"],
        "major_level": info["major_level"],
        "current_xp": info["current_exp"],
        "next_level_xp": limit,
        "progress_percent": info["progress_percent"],
    }


def check_level_up(old_level: str, new_level: str) -> bool:
    return old_level != new_level


async def award_badge_if_earned(db, user_id: int, condition_type: str, value: int) -> list:
    """Check if user earned new badges. Returns list of newly earned badge dicts."""
    from sqlalchemy import select
    earned = []
    result = await db.execute(select(Badge).where(Badge.condition_type == condition_type, Badge.condition_value <= value))
    badges = result.scalars().all()
    for b in badges:
        existing = await db.execute(
            select(UserBadge).where(UserBadge.user_id == user_id, UserBadge.badge_id == b.id)
        )
        if not existing.scalar_one_or_none():
            db.add(UserBadge(user_id=user_id, badge_id=b.id))
            earned.append({"id": b.id, "name": b.name, "description": b.description, "icon_url": b.icon_url})
    if earned:
        await db.flush()
    return earned


async def get_consecutive_days(db, user_id: int) -> int:
    """Count consecutive login days from user_daily_tasks records."""
    from sqlalchemy import select, desc
    from app.models.gamification import UserDailyTask
    today = datetime.date.today()
    result = await db.execute(
        select(UserDailyTask.date)
        .where(UserDailyTask.user_id == user_id, UserDailyTask.is_completed == True)
        .order_by(desc(UserDailyTask.date))
    )
    dates = [row[0] for row in result.all()]
    if not dates:
        return 0
    streak = 0
    check = today
    for d in dates:
        if d == check or d == check - datetime.timedelta(days=1):
            streak += 1
            check = d
        else:
            break
    return streak


async def get_today_practice_exp(db, user_id: int) -> int:
    """Sum EXP earned from practice records created today."""
    from sqlalchemy import select, func
    from app.models.gamification import PracticeRecord
    today = datetime.date.today()
    result = await db.execute(
        select(func.coalesce(func.sum(PracticeRecord.score), 0))
        .where(
            PracticeRecord.user_id == user_id,
            func.date(PracticeRecord.created_at) == today,
        )
    )
    return result.scalar() or 0


def reset_daily_exp_if_new_day(user) -> bool:
    """Reset daily_exp if it's a new day. Returns True if reset occurred."""
    today = datetime.date.today()
    if user.daily_exp_date != today:
        user.daily_exp = 0
        user.daily_exp_date = today
        return True
    return False
