from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.favorite import Favorite
from app.schemas.common import api_response

router = APIRouter()


class FavoriteCreate(BaseModel):
    item_type: str = Field(..., description="course / question")
    item_id: str
    title: str = ""


@router.get("")
async def list_favorites(
    item_type: str = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Favorite).where(Favorite.user_id == user.id)
    if item_type:
        q = q.where(Favorite.item_type == item_type)
    q = q.order_by(Favorite.created_at.desc())
    result = await db.execute(q)
    favorites = result.scalars().all()
    return api_response(data=[
        {"id": f.id, "item_type": f.item_type, "item_id": f.item_id, "title": f.title, "created_at": str(f.created_at)}
        for f in favorites
    ])


@router.post("")
async def add_favorite(
    req: FavoriteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(
        select(Favorite).where(
            Favorite.user_id == user.id,
            Favorite.item_type == req.item_type,
            Favorite.item_id == req.item_id,
        )
    )).scalar_one_or_none()
    if existing:
        return api_response(400, "已收藏")

    fav = Favorite(user_id=user.id, item_type=req.item_type, item_id=req.item_id, title=req.title)
    db.add(fav)
    await db.commit()
    await db.refresh(fav)
    return api_response(data={"id": fav.id, "item_type": fav.item_type, "item_id": fav.item_id})


@router.delete("/{favorite_id}")
async def remove_favorite(
    favorite_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fav = (await db.execute(
        select(Favorite).where(Favorite.id == favorite_id, Favorite.user_id == user.id)
    )).scalar_one_or_none()
    if not fav:
        return api_response(404, "收藏不存在")
    await db.delete(fav)
    await db.commit()
    return api_response(data={"message": "已取消收藏"})


@router.delete("/item/{item_type}/{item_id}")
async def remove_favorite_by_item(
    item_type: str,
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fav = (await db.execute(
        select(Favorite).where(
            Favorite.user_id == user.id,
            Favorite.item_type == item_type,
            Favorite.item_id == item_id,
        )
    )).scalar_one_or_none()
    if fav:
        await db.delete(fav)
        await db.commit()
    return api_response(data={"message": "已取消收藏"})
