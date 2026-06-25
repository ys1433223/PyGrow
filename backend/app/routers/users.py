from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.course import CourseCollection
from app.schemas.user import UserProfileUpdate
from app.schemas.common import api_response

router = APIRouter()


@router.get("/profile")
async def get_profile(user: User = Depends(get_current_user)):
    return api_response(data={
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "avatar": user.avatar,
        "email": user.email,
    })


@router.put("/profile")
async def update_profile(req: UserProfileUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if req.nickname is not None:
        user.nickname = req.nickname
    if req.avatar is not None:
        user.avatar = req.avatar
    await db.commit()
    await db.refresh(user)
    return api_response(data={
        "id": user.id,
        "nickname": user.nickname,
        "avatar": user.avatar,
    })


@router.get("/collections")
async def get_collections(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CourseCollection).where(CourseCollection.user_id == user.id)
    )
    collections = result.scalars().all()
    return api_response(data=[c.course_id for c in collections])


@router.post("/collections/{course_id}")
async def toggle_collection(course_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CourseCollection).where(
            CourseCollection.user_id == user.id,
            CourseCollection.course_id == course_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        await db.delete(existing)
        await db.commit()
        return api_response(message="已取消收藏", data={"collected": False})
    else:
        coll = CourseCollection(user_id=user.id, course_id=course_id)
        db.add(coll)
        await db.commit()
        return api_response(message="收藏成功", data={"collected": True})
