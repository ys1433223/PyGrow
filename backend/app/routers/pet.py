from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.common import api_response
from app.services.pet_service import (
    start_adventure,
    get_current_adventure,
    claim_adventure_reward,
    get_adventure_logs,
    get_cookie_records,
    get_user_rewards,
    mark_reward_seen,
    get_or_create_pet_profile,
    reset_daily_cookies_if_new_day,
)

router = APIRouter()


@router.get("/profile")
async def get_pet_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get pet profile: status, cookies, and current adventure info."""
    reset_daily_cookies_if_new_day(user)
    profile = await get_or_create_pet_profile(user.id, db)

    data = {
        "pet_id": profile.id,
        "pet_name": profile.pet_name,
        "pet_type": profile.pet_type,
        "status": profile.status,
        "cookies": user.cookies or 0,
        "daily_cookies": user.daily_cookies or 0,
        "daily_cookie_cap": 30,
        "adventure_cost": 3,
    }

    if profile.status in ("exploring", "completed"):
        adv_info = await get_current_adventure(user, db)
        data.update({
            "has_adventure": adv_info.get("has_adventure", False),
            "adventure_location": adv_info.get("adventure_location"),
            "adventure_status": adv_info.get("status"),
            "remaining_seconds": adv_info.get("remaining_seconds", 0),
            "adventure_message": adv_info.get("message", ""),
        })

    return api_response(data=data)


@router.post("/adventure/start")
async def start_pet_adventure(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a one-click random adventure. Costs 3 cookies."""
    result = await start_adventure(user, db)
    await db.commit()

    if result["success"]:
        return api_response(data=result)
    else:
        return api_response(400, result["message"], data=result)


@router.get("/adventure/current")
async def current_adventure(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current adventure status. If adventure time is up, status changes to completed."""
    result = await get_current_adventure(user, db)
    await db.commit()
    return api_response(data=result)


@router.post("/adventure/claim")
async def claim_reward(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Claim reward for a completed adventure. Generates postcard/knowledge_note/blessing."""
    result = await claim_adventure_reward(user, db)
    await db.commit()

    if result["success"]:
        return api_response(data=result)
    else:
        return api_response(400, result["message"], data=result)


@router.get("/adventure/logs")
async def adventure_logs(
    limit: int = Query(20, ge=5, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get adventure history logs with reward details."""
    logs = await get_adventure_logs(user.id, db, limit)
    return api_response(data={
        "logs": logs,
        "total": len(logs),
    })


@router.get("/rewards")
async def rewards_backpack(
    reward_type: str = Query(None, description="Filter: postcard / knowledge_note / blessing"),
    limit: int = Query(50, ge=5, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's reward backpack, optionally filtered by type.

    Returns rewards grouped by type:
    - postcards: list of postcard rewards
    - knowledge_notes: list of knowledge_note rewards
    - blessings: list of blessing rewards
    """
    rewards = await get_user_rewards(user.id, db, reward_type, limit)

    # Group by type
    postcards = [r for r in rewards if r["reward_type"] == "postcard"]
    knowledge_notes = [r for r in rewards if r["reward_type"] == "knowledge_note"]
    blessings = [r for r in rewards if r["reward_type"] == "blessing"]

    return api_response(data={
        "rewards": rewards,
        "total": len(rewards),
        "postcards": postcards,
        "knowledge_notes": knowledge_notes,
        "blessings": blessings,
        "counts": {
            "postcard": len(postcards),
            "knowledge_note": len(knowledge_notes),
            "blessing": len(blessings),
        },
    })


@router.post("/rewards/seen")
async def mark_reward_as_seen(
    reward_id: int = Query(..., description="Reward ID to mark as seen"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a reward as seen (is_new = 0)."""
    ok = await mark_reward_seen(user.id, reward_id, db)
    if ok:
        await db.commit()
        return api_response(data={"message": "已标记为已查看"})
    else:
        return api_response(404, "奖励不存在")


@router.get("/cookie-records")
async def cookie_records(
    limit: int = Query(50, ge=5, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get cookie transaction records (earning and spending history)."""
    records = await get_cookie_records(user.id, db, limit)
    return api_response(data={
        "records": records,
        "total": len(records),
    })
