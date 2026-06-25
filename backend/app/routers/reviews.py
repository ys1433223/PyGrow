from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.review import CourseReview
from app.schemas.common import api_response

router = APIRouter()


class ReviewCreate(BaseModel):
    course_id: str = Field(..., description="初级/中级/高级")
    rating: int = Field(..., ge=1, le=5)
    content: str = ""


@router.get("/{course_id}")
async def list_reviews(course_id: str, db: AsyncSession = Depends(get_db)):
    """List reviews for a course. Public."""
    result = await db.execute(
        select(
            CourseReview.id,
            CourseReview.rating,
            CourseReview.content,
            CourseReview.created_at,
            User.username.label("username"),
            User.avatar.label("avatar"),
        )
        .join(User, User.id == CourseReview.user_id)
        .where(CourseReview.course_id == course_id)
        .order_by(CourseReview.created_at.desc())
        .limit(50)
    )
    rows = result.all()

    # Aggregate stats
    stats_result = await db.execute(
        select(
            func.count(CourseReview.id),
            func.coalesce(func.avg(CourseReview.rating), 0),
        ).where(CourseReview.course_id == course_id)
    )
    count, avg_rating = stats_result.one()

    return api_response(data={
        "reviews": [
            {
                "id": r.id,
                "rating": r.rating,
                "content": r.content,
                "username": r.username,
                "avatar": r.avatar,
                "created_at": str(r.created_at),
            }
            for r in rows
        ],
        "count": count,
        "avg_rating": round(float(avg_rating), 1),
    })


@router.post("")
async def create_review(
    req: ReviewCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a course review. One review per user per course."""
    existing = (
        await db.execute(
            select(CourseReview).where(
                CourseReview.user_id == user.id,
                CourseReview.course_id == req.course_id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        return api_response(400, "你已评价过该课程")

    review = CourseReview(
        user_id=user.id,
        course_id=req.course_id,
        rating=req.rating,
        content=req.content,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    return api_response(data={
        "id": review.id,
        "rating": review.rating,
        "content": review.content,
        "created_at": str(review.created_at),
    })
