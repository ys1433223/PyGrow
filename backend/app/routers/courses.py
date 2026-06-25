from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.course import Course, Lesson, CourseProgress
from app.schemas.course import CourseDetailOut, ProgressUpdate
from app.schemas.common import api_response
from app.services.gamification import calc_level, award_badge_if_earned

router = APIRouter()


@router.get("")
async def list_courses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).order_by(Course.sort_order))
    courses = result.scalars().all()
    return api_response(data=[
        {
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "category": c.category,
            "category_color": c.category_color,
            "icon": c.icon,
            "cover_color": c.cover_color,
            "bvid": c.bvid,
            "sort_order": c.sort_order,
        }
        for c in courses
    ])


@router.get("/{course_id}")
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Course).where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    if not course:
        return api_response(404, "课程不存在")

    lessons_result = await db.execute(
        select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.sort_order)
    )
    lessons = lessons_result.scalars().all()

    return api_response(data={
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "category": course.category,
        "category_color": course.category_color,
        "icon": course.icon,
        "cover_color": course.cover_color,
        "bvid": course.bvid,
        "sort_order": course.sort_order,
        "lessons": [
            {
                "id": l.id,
                "title": l.title,
                "chapter": l.chapter,
                "duration": l.duration,
                "bilibili_page": l.bilibili_page,
                "sort_order": l.sort_order,
            }
            for l in lessons
        ],
    })


@router.get("/{course_id}/progress")
async def get_progress(course_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CourseProgress).where(
            CourseProgress.user_id == user.id,
            CourseProgress.course_id == course_id,
        )
    )
    progress = result.scalar_one_or_none()
    if not progress:
        return api_response(data={"last_lesson_id": None, "progress_percent": 0, "is_completed": False})
    return api_response(data={
        "last_lesson_id": progress.last_lesson_id,
        "progress_percent": progress.progress_percent,
        "is_completed": progress.is_completed,
    })


@router.post("/{course_id}/progress")
async def update_progress(
    course_id: int,
    req: ProgressUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CourseProgress).where(
            CourseProgress.user_id == user.id,
            CourseProgress.course_id == course_id,
        )
    )
    progress = result.scalar_one_or_none()
    if not progress:
        progress = CourseProgress(user_id=user.id, course_id=course_id)
        db.add(progress)

    if req.last_lesson_id is not None:
        progress.last_lesson_id = req.last_lesson_id
    if req.progress_percent is not None:
        progress.progress_percent = req.progress_percent
    was_completed = progress.is_completed
    if req.is_completed is not None:
        progress.is_completed = req.is_completed

    await db.flush()

    xp_gained = 0
    new_badges = []
    if progress.is_completed and not was_completed:
        user.experience += 10
        user.points += 10
        old_level = user.level
        user.level = calc_level(user.experience)
        xp_gained = 10
        new_badges = await award_badge_if_earned(db, user.id, "course_complete", 1)

    await db.commit()
    return api_response(data={"message": "进度已更新", "experience_gained": xp_gained, "new_badges": new_badges})
