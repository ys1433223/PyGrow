import os
import random
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user import User

DAILY_COOKIE_CAP = 30
ADVENTURE_COST = 3
ADVENTURE_DURATION_SECONDS = 5

ADVENTURE_LOCATIONS = [
    "校园小路", "森林书屋", "星空营地", "海边车站", "樱花小镇",
    "雪山邮局", "代码城市", "云朵牧场", "晚风码头", "极光山谷",
]

# ---- Reward probabilities ----
REWARD_PROBABILITIES = {
    "postcard": 0.50,
    "knowledge_note": 0.35,
    "blessing": 0.15,
}

# ---- Postcard blessings (for reward_content on postcards) ----
POSTCARD_BLESSINGS = [
    "今天也在一点点变强，继续保持呀！",
    "学习辛苦啦，这张远方的风景送给认真努力的你。",
    "每一次练习，都是通向更强自己的小小一步。",
    "慢一点也没关系，你一直在前进。",
    "代码也许会报错，但努力不会白费。",
    "愿你今天的学习像这片风景一样明亮。",
    "小宠物从远方给你带回了一点好运气。",
    "别急，慢慢来，知识会一点点长出来。",
    "你已经完成了今天的一段旅程，很棒！",
    "愿这张明信片给你带来继续学习的力量。",
    "这份远方的风，送给今天认真学习的你。",
    "你写下的每一行代码，都会慢慢变成能力。",
    "今天的努力已经被好好记录下来啦。",
    "别怕报错，调试也是成长的一部分。",
    "愿你在下一次练习里更从容一点。",
]

# ---- Knowledge note pool ----
KNOWLEDGE_NOTES = [
    "input() 获取到的内容默认是字符串。",
    "for 循环适合处理已知次数的重复任务。",
    "append() 会把元素添加到列表末尾。",
    "函数可以减少重复代码，提高程序复用性。",
    "字典适合保存键值对形式的数据。",
    "缩进是 Python 代码结构的一部分，不能随意省略。",
    "if 语句用于根据条件决定程序是否执行某段代码。",
    "列表适合保存一组有顺序的数据。",
    "while 循环适合处理循环次数不确定的情况。",
    "return 用于把函数处理后的结果返回给调用者。",
    "字符串可以用 + 拼接，也可以用 f\"...\" 格式化。",
    "try/except 可以捕获异常，防止程序崩溃。",
    "import 用于导入模块，复用别人写好的功能。",
    "range(5) 生成 0 到 4 的整数序列。",
    "len() 可以获取字符串、列表、字典等数据的长度。",
    "列表推导式 [x*2 for x in nums] 可以简洁地创建列表。",
    "字典的 get() 方法可以安全地获取值，键不存在时返回 None。",
    "集合 set 可以自动去重，适合处理不重复的元素。",
    "文件操作后记得用 close() 或用 with 语句自动关闭。",
    "Python 中用 # 写单行注释，用三个引号写多行注释。",
]

# ---- Blessing pool (for blessing-type rewards) ----
BLESSINGS = [
    "今天的努力已经被好好记录下来啦。",
    "你已经完成了今天的一段旅程，很棒！",
    "慢一点也没关系，你一直在前进。",
    "愿你在下一次练习里更从容一点。",
    "学习不是一口气跑完，而是每天多走一步。",
    "这次练习可能不完美，但你已经在变强了。",
    "继续保持，你的代码能力正在一点点长出来。",
    "小宠物给你带回了一点继续学习的勇气。",
    "别给自己太大压力，你已经很努力了。",
    "今天也辛苦啦，记得给自己一点奖励。",
    "每一个报错都是学习的机会，不要怕它。",
    "编程的路上有晴天也有雨天，但每一步都算数。",
]


def _get_scenery_dir() -> str:
    """Resolve the absolute path to the Scenery postcard image folder."""
    service_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(service_dir))
    return os.path.join(project_root, "..", "frontend", "public", "pets", "Scenery")


SCENERY_DIR = _get_scenery_dir()


def list_scenery_images() -> list[str]:
    """List all image filenames in the Scenery directory."""
    if not os.path.isdir(SCENERY_DIR):
        return []
    files = os.listdir(SCENERY_DIR)
    return sorted([f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))])


def pick_random_location() -> str:
    return random.choice(ADVENTURE_LOCATIONS)


def pick_reward_type() -> str:
    """Pick reward type based on configured probabilities."""
    r = random.random()
    cumulative = 0.0
    for rtype, prob in REWARD_PROBABILITIES.items():
        cumulative += prob
        if r < cumulative:
            return rtype
    return "knowledge_note"  # fallback


def generate_adventure_reward(adventure_location: str) -> dict:
    """Generate a reward for a completed adventure.

    Returns a dict with reward fields ready for PetReward creation.
    Falls back to knowledge_note if postcard image directory is empty.
    """
    reward_type = pick_reward_type()

    if reward_type == "postcard":
        images = list_scenery_images()
        if images:
            image_file = random.choice(images)
            location_name = os.path.splitext(image_file)[0]
            image_url = f"/pets/Scenery/{image_file}"
            blessing = random.choice(POSTCARD_BLESSINGS)
            return {
                "reward_type": "postcard",
                "reward_name": f"来自「{location_name}」的明信片",
                "reward_content": blessing,
                "reward_image": image_url,
                "rarity": "common",
                "source_location": location_name,
            }
        else:
            # Fallback: no images available, give knowledge_note instead
            reward_type = "knowledge_note"

    if reward_type == "knowledge_note":
        note = random.choice(KNOWLEDGE_NOTES)
        return {
            "reward_type": "knowledge_note",
            "reward_name": "知识点小纸条",
            "reward_content": note,
            "reward_image": None,
            "rarity": "common",
            "source_location": adventure_location,
        }

    if reward_type == "blessing":
        blessing = random.choice(BLESSINGS)
        return {
            "reward_type": "blessing",
            "reward_name": "小祝福",
            "reward_content": blessing,
            "reward_image": None,
            "rarity": "common",
            "source_location": adventure_location,
        }

    # Should not reach here, but fallback
    note = random.choice(KNOWLEDGE_NOTES)
    return {
        "reward_type": "knowledge_note",
        "reward_name": "知识点小纸条",
        "reward_content": note,
        "reward_image": None,
        "rarity": "common",
        "source_location": adventure_location,
    }


def reset_daily_cookies_if_new_day(user: User) -> bool:
    """Reset daily_cookies if it's a new day. Returns True if reset occurred."""
    today = datetime.date.today()
    if user.daily_cookies_date != today:
        user.daily_cookies = 0
        user.daily_cookies_date = today
        return True
    return False


async def award_cookies(
    db: AsyncSession,
    user: User,
    amount: int,
    source_type: str,
    description: str,
) -> int:
    """Award cookies to user, respecting daily cap. Returns actual amount awarded."""
    from app.models.pet import PetCookieRecord

    if amount <= 0:
        return 0

    reset_daily_cookies_if_new_day(user)

    available = DAILY_COOKIE_CAP - (user.daily_cookies or 0)
    actual = min(amount, available)

    if actual <= 0:
        return 0

    user.cookies = (user.cookies or 0) + actual
    user.daily_cookies = (user.daily_cookies or 0) + actual

    db.add(PetCookieRecord(
        user_id=user.id,
        source_type=source_type,
        cookies=actual,
        description=description,
    ))

    return actual


async def spend_cookies(
    db: AsyncSession,
    user: User,
    amount: int,
    source_type: str,
    description: str,
) -> bool:
    """Spend cookies. Returns True if successful, False if insufficient."""
    from app.models.pet import PetCookieRecord

    if (user.cookies or 0) < amount:
        return False

    user.cookies -= amount
    db.add(PetCookieRecord(
        user_id=user.id,
        source_type=source_type,
        cookies=-amount,
        description=description,
    ))
    return True


async def get_or_create_pet_profile(user_id: int, db: AsyncSession):
    """Get existing pet profile or create a default one."""
    from app.models.pet import PetProfile

    result = await db.execute(
        select(PetProfile).where(PetProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = PetProfile(user_id=user_id)
        db.add(profile)
        await db.flush()

    return profile


async def start_adventure(user: User, db: AsyncSession) -> dict:
    """Start a one-click random adventure. Returns result dict."""
    from app.models.pet import PetProfile, PetAdventure

    profile = await get_or_create_pet_profile(user.id, db)

    if profile.status == "exploring":
        if profile.current_adventure_id:
            adv_result = await db.execute(
                select(PetAdventure).where(PetAdventure.id == profile.current_adventure_id)
            )
            adv = adv_result.scalar_one_or_none()
            if adv and adv.status == "exploring":
                now = datetime.datetime.utcnow()
                if now < adv.end_time:
                    remaining = int((adv.end_time - now).total_seconds())
                    return {
                        "success": False,
                        "code": "already_exploring",
                        "message": f"宠物正在探险中，还需等待 {remaining} 秒",
                        "remaining_seconds": remaining,
                        "adventure_location": adv.adventure_location,
                    }
                else:
                    adv.status = "completed"
                    profile.status = "completed"
                    await db.flush()

    current_cookies = user.cookies or 0
    if current_cookies < ADVENTURE_COST:
        shortage = ADVENTURE_COST - current_cookies
        return {
            "success": False,
            "code": "insufficient_cookies",
            "message": f"饼干不足！当前拥有 {current_cookies} 个饼干，还需要 {shortage} 个饼干（每次探险消耗 {ADVENTURE_COST} 个）",
            "current_cookies": current_cookies,
            "required": ADVENTURE_COST,
            "shortage": shortage,
        }

    spent = await spend_cookies(
        db, user, ADVENTURE_COST,
        source_type="adventure_cost",
        description=f"派宠物去探险，消耗 {ADVENTURE_COST} 个饼干",
    )
    if not spent:
        return {
            "success": False,
            "code": "insufficient_cookies",
            "message": f"饼干不足！当前拥有 {current_cookies} 个饼干",
            "current_cookies": current_cookies,
            "required": ADVENTURE_COST,
        }

    location = pick_random_location()
    now = datetime.datetime.utcnow()
    end_time = now + datetime.timedelta(seconds=ADVENTURE_DURATION_SECONDS)

    adventure = PetAdventure(
        user_id=user.id,
        pet_id=profile.id,
        adventure_location=location,
        cost_cookies=ADVENTURE_COST,
        status="exploring",
        start_time=now,
        end_time=end_time,
    )
    db.add(adventure)
    await db.flush()

    profile.status = "exploring"
    profile.current_adventure_id = adventure.id
    await db.flush()

    return {
        "success": True,
        "message": f"宠物出发去「{location}」探险啦！",
        "adventure_id": adventure.id,
        "adventure_location": location,
        "cost_cookies": ADVENTURE_COST,
        "start_time": str(adventure.start_time),
        "end_time": str(adventure.end_time),
        "duration_seconds": ADVENTURE_DURATION_SECONDS,
        "remaining_cookies": user.cookies,
    }


async def get_current_adventure(user: User, db: AsyncSession) -> dict:
    """Get current adventure status for the user."""
    from app.models.pet import PetProfile, PetAdventure

    profile = await get_or_create_pet_profile(user.id, db)

    if profile.status in ("idle", None):
        return {
            "has_adventure": False,
            "status": "idle",
            "message": "宠物待机中，可以派去探险",
            "cookies": user.cookies or 0,
        }

    adventure = None
    if profile.current_adventure_id:
        result = await db.execute(
            select(PetAdventure).where(PetAdventure.id == profile.current_adventure_id)
        )
        adventure = result.scalar_one_or_none()

    if not adventure:
        profile.status = "idle"
        profile.current_adventure_id = None
        await db.flush()
        return {
            "has_adventure": False,
            "status": "idle",
            "message": "宠物待机中",
            "cookies": user.cookies or 0,
        }

    now = datetime.datetime.utcnow()

    if adventure.status == "exploring" and now >= adventure.end_time:
        adventure.status = "completed"
        profile.status = "completed"
        await db.flush()

    remaining = 0
    if adventure.status == "exploring" and now < adventure.end_time:
        remaining = int((adventure.end_time - now).total_seconds())

    return {
        "has_adventure": True,
        "adventure_id": adventure.id,
        "adventure_location": adventure.adventure_location,
        "status": adventure.status,
        "pet_status": profile.status,
        "start_time": str(adventure.start_time),
        "end_time": str(adventure.end_time),
        "remaining_seconds": remaining,
        "cost_cookies": adventure.cost_cookies,
        "cookies": user.cookies or 0,
        "message": (
            f"宠物正在「{adventure.adventure_location}」探险中，还需等待 {remaining} 秒"
            if adventure.status == "exploring" and remaining > 0
            else f"宠物从「{adventure.adventure_location}」回来了！点击领取奖励"
            if adventure.status == "completed"
            else "奖励已领取"
        ),
    }


async def claim_adventure_reward(user: User, db: AsyncSession) -> dict:
    """Claim reward for a completed adventure. Generates postcard/knowledge_note/blessing."""
    from app.models.pet import PetProfile, PetAdventure, PetReward

    profile = await get_or_create_pet_profile(user.id, db)

    if profile.status != "completed":
        return {
            "success": False,
            "code": "no_completed_adventure",
            "message": "没有可领取奖励的探险" if profile.status != "exploring" else "宠物还在探险中，请等待探险完成后再领取奖励",
        }

    if not profile.current_adventure_id:
        profile.status = "idle"
        await db.flush()
        return {"success": False, "code": "no_adventure", "message": "没有探险记录"}

    result = await db.execute(
        select(PetAdventure).where(PetAdventure.id == profile.current_adventure_id)
    )
    adventure = result.scalar_one_or_none()

    if not adventure or adventure.status == "claimed":
        profile.status = "idle"
        profile.current_adventure_id = None
        await db.flush()
        return {"success": False, "code": "already_claimed", "message": "奖励已领取"}

    # Generate reward
    reward_data = generate_adventure_reward(adventure.adventure_location)

    # Create PetReward record
    pet_reward = PetReward(
        user_id=user.id,
        adventure_id=adventure.id,
        reward_type=reward_data["reward_type"],
        reward_name=reward_data["reward_name"],
        reward_content=reward_data["reward_content"],
        reward_image=reward_data["reward_image"],
        rarity=reward_data["rarity"],
        source_location=reward_data["source_location"],
        is_new=1,
    )
    db.add(pet_reward)
    await db.flush()

    # Mark adventure as claimed
    adventure.status = "claimed"
    adventure.reward_type = reward_data["reward_type"]
    adventure.reward_description = reward_data["reward_name"]

    # Reset pet profile
    profile.status = "idle"
    profile.current_adventure_id = None

    await db.flush()

    return {
        "success": True,
        "message": f"宠物从「{adventure.adventure_location}」探险归来！获得了{reward_data['reward_name']}",
        "reward": {
            "id": pet_reward.id,
            "reward_type": reward_data["reward_type"],
            "reward_name": reward_data["reward_name"],
            "reward_content": reward_data["reward_content"],
            "reward_image": reward_data["reward_image"],
            "rarity": reward_data["rarity"],
            "source_location": reward_data["source_location"],
            "is_new": True,
        },
        "adventure_location": adventure.adventure_location,
        "cookies": user.cookies,
    }


async def get_user_rewards(
    user_id: int,
    db: AsyncSession,
    reward_type: str = None,
    limit: int = 50,
) -> list:
    """Get user's reward backpack, optionally filtered by type."""
    from app.models.pet import PetReward

    stmt = select(PetReward).where(PetReward.user_id == user_id)
    if reward_type:
        stmt = stmt.where(PetReward.reward_type == reward_type)
    stmt = stmt.order_by(PetReward.created_at.desc()).limit(limit)

    result = await db.execute(stmt)
    rewards = result.scalars().all()

    return [
        {
            "id": r.id,
            "reward_type": r.reward_type,
            "reward_name": r.reward_name,
            "reward_content": r.reward_content,
            "reward_image": r.reward_image,
            "rarity": r.rarity,
            "source_location": r.source_location,
            "is_new": bool(r.is_new),
            "created_at": str(r.created_at),
        }
        for r in rewards
    ]


async def mark_reward_seen(user_id: int, reward_id: int, db: AsyncSession) -> bool:
    """Mark a reward as seen (is_new = 0)."""
    from app.models.pet import PetReward

    result = await db.execute(
        select(PetReward).where(
            PetReward.id == reward_id,
            PetReward.user_id == user_id,
        )
    )
    reward = result.scalar_one_or_none()
    if reward:
        reward.is_new = 0
        return True
    return False


async def get_adventure_logs(user_id: int, db: AsyncSession, limit: int = 20) -> list:
    """Get adventure history for a user, including reward info."""
    from app.models.pet import PetAdventure, PetReward

    result = await db.execute(
        select(PetAdventure)
        .where(PetAdventure.user_id == user_id)
        .order_by(PetAdventure.created_at.desc())
        .limit(limit)
    )
    adventures = result.scalars().all()

    logs = []
    for a in adventures:
        log = {
            "id": a.id,
            "adventure_location": a.adventure_location,
            "cost_cookies": a.cost_cookies,
            "status": a.status,
            "start_time": str(a.start_time),
            "end_time": str(a.end_time),
            "reward_type": a.reward_type,
            "reward_description": a.reward_description,
        }
        # Include reward details if claimed
        if a.status == "claimed":
            reward_result = await db.execute(
                select(PetReward).where(PetReward.adventure_id == a.id)
            )
            reward = reward_result.scalar_one_or_none()
            if reward:
                log["reward"] = {
                    "id": reward.id,
                    "reward_type": reward.reward_type,
                    "reward_name": reward.reward_name,
                    "reward_content": reward.reward_content,
                    "reward_image": reward.reward_image,
                    "rarity": reward.rarity,
                    "source_location": reward.source_location,
                }
        logs.append(log)

    return logs


async def get_cookie_records(user_id: int, db: AsyncSession, limit: int = 50) -> list:
    """Get cookie transaction history for a user."""
    from app.models.pet import PetCookieRecord

    result = await db.execute(
        select(PetCookieRecord)
        .where(PetCookieRecord.user_id == user_id)
        .order_by(PetCookieRecord.created_at.desc())
        .limit(limit)
    )
    records = result.scalars().all()

    return [
        {
            "id": r.id,
            "source_type": r.source_type,
            "cookies": r.cookies,
            "description": r.description,
            "created_at": str(r.created_at),
        }
        for r in records
    ]
