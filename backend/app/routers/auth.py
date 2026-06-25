from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.common import api_response
from app.models.user import User
from app.models.gamification import UserBadge, Badge, PracticeRecord
from app.services.auth_service import hash_password, verify_password, create_access_token, get_user_by_username
from app.services.gamification import award_badge_if_earned, reset_daily_exp_if_new_day, calc_rank_progress

router = APIRouter()


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if req.password != req.confirm_password:
        return api_response(400, "两次密码不一致")

    existing = await get_user_by_username(db, req.username)
    if existing:
        return api_response(400, "用户名已存在")

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        nickname=req.username,
        avatar=f"https://api.dicebear.com/7.x/avataaars/svg?seed={req.username}",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    user.last_login_at = datetime.now()
    await db.flush()
    await award_badge_if_earned(db, user.id, "login_first", 1)
    await db.commit()

    assess_check = await db.execute(select(PracticeRecord).where(PracticeRecord.user_id == user.id).limit(1))
    has_assessment = assess_check.scalar_one_or_none() is not None

    token = create_access_token({"sub": str(user.id)})
    return api_response(200, "注册成功", {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id, "name": user.nickname or user.username, "avatar": user.avatar,
            "level": user.current_rank, "experience": user.total_exp or 0,
            "current_rank": user.current_rank, "current_exp": user.current_exp or 0,
            "rank_exp_limit": user.rank_exp_limit or 100, "total_exp": user.total_exp or 0,
            "cookies": user.cookies or 0, "has_assessment": has_assessment,
        },
    })


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_username(db, req.username)
    if not user or not verify_password(req.password, user.password_hash):
        return api_response(401, "用户名或密码错误")

    user.last_login_at = datetime.now()
    reset_daily_exp_if_new_day(user)
    await db.flush()
    await award_badge_if_earned(db, user.id, "login_first", 1)
    await db.commit()

    assess_check = await db.execute(select(PracticeRecord).where(PracticeRecord.user_id == user.id).limit(1))
    has_assessment = assess_check.scalar_one_or_none() is not None

    token = create_access_token({"sub": str(user.id)})
    return api_response(200, "登录成功", {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id, "name": user.nickname or user.username, "avatar": user.avatar,
            "level": user.current_rank or "萌新小白", "experience": user.total_exp or 0,
            "current_rank": user.current_rank or "萌新小白", "current_exp": user.current_exp or 0,
            "rank_exp_limit": user.rank_exp_limit or 100, "total_exp": user.total_exp or 0,
            "cookies": user.cookies or 0, "has_assessment": has_assessment,
        },
    })


