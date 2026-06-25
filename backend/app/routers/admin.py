from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.course import Course
from app.models.gamification import Question, Badge, DailyTask
from app.models.project import Project
from app.models.community import Post
from app.schemas.common import api_response

router = APIRouter()


async def require_admin(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


# ==================== Users ====================

@router.get("/users")
async def admin_users(
    page: int = 1,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset((page - 1) * 20).limit(20)
    )
    users = result.scalars().all()
    total = (await db.execute(select(func.count(User.id)))).scalar()

    return api_response(data={
        "users": [
            {"id": u.id, "username": u.username, "email": u.email,
             "level": u.level, "experience": u.experience, "points": u.points,
             "is_admin": bool(u.is_admin), "created_at": str(u.created_at)}
            for u in users
        ],
        "total": total,
    })


@router.post("/users/{user_id}/toggle-admin")
async def toggle_admin(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    u = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not u:
        return api_response(404, "用户不存在")
    u.is_admin = 1 if not u.is_admin else 0
    await db.commit()
    return api_response(data={"is_admin": bool(u.is_admin)})


# ==================== Courses ====================

@router.get("/courses")
async def admin_courses(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).order_by(Course.sort_order))
    courses = result.scalars().all()
    return api_response(data=[{"id": c.id, "title": c.title, "category": c.category, "sort_order": c.sort_order} for c in courses])


@router.post("/courses")
async def create_course(req: dict, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    course = Course(**req)
    db.add(course)
    await db.commit()
    return api_response(data={"id": course.id})


@router.put("/courses/{course_id}")
async def update_course(course_id: int, req: dict, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    course = (await db.execute(select(Course).where(Course.id == course_id))).scalar_one_or_none()
    if not course:
        return api_response(404, "课程不存在")
    for k, v in req.items():
        if hasattr(course, k):
            setattr(course, k, v)
    await db.commit()
    return api_response(data={"message": "更新成功"})


@router.delete("/courses/{course_id}")
async def delete_course(course_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    course = (await db.execute(select(Course).where(Course.id == course_id))).scalar_one_or_none()
    if not course:
        return api_response(404, "课程不存在")
    await db.delete(course)
    await db.commit()
    return api_response(data={"message": "已删除"})


# ==================== Questions ====================

@router.get("/questions")
async def admin_questions(page: int = 1, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Question).order_by(Question.created_at.desc()).offset((page - 1) * 20).limit(20)
    )
    questions = result.scalars().all()
    total = (await db.execute(select(func.count(Question.id)))).scalar()
    return api_response(data={
        "questions": [{"id": q.id, "title": q.title, "type": q.type, "knowledge_point": q.knowledge_point, "difficulty": q.difficulty, "level": q.level} for q in questions],
        "total": total,
    })


@router.post("/questions")
async def create_question(req: dict, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    q = Question(**req)
    db.add(q)
    await db.commit()
    return api_response(data={"id": q.id})


@router.put("/questions/{question_id}")
async def update_question(question_id: int, req: dict, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    q = (await db.execute(select(Question).where(Question.id == question_id))).scalar_one_or_none()
    if not q:
        return api_response(404, "题目不存在")
    for k, v in req.items():
        if hasattr(q, k):
            setattr(q, k, v)
    await db.commit()
    return api_response(data={"message": "更新成功"})


@router.delete("/questions/{question_id}")
async def delete_question(question_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    q = (await db.execute(select(Question).where(Question.id == question_id))).scalar_one_or_none()
    if not q:
        return api_response(404, "题目不存在")
    await db.delete(q)
    await db.commit()
    return api_response(data={"message": "已删除"})


# ==================== Projects ====================

@router.get("/projects")
async def admin_projects(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    return api_response(data=[{"id": p.id, "title": p.title, "level": p.level, "category": p.category} for p in projects])


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p:
        return api_response(404, "项目不存在")
    await db.delete(p)
    await db.commit()
    return api_response(data={"message": "已删除"})


# ==================== Posts ====================

@router.get("/posts")
async def admin_posts(page: int = 1, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Post).order_by(Post.created_at.desc()).offset((page - 1) * 20).limit(20)
    )
    posts = result.scalars().all()
    total = (await db.execute(select(func.count(Post.id)))).scalar()
    return api_response(data={
        "posts": [{"id": p.id, "title": p.title, "category": p.category, "created_at": str(p.created_at)} for p in posts],
        "total": total,
    })


@router.delete("/posts/{post_id}")
async def delete_post(post_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not p:
        return api_response(404, "帖子不存在")
    await db.delete(p)
    await db.commit()
    return api_response(data={"message": "已删除"})


# ==================== Stats ====================

@router.get("/stats")
async def admin_stats(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    user_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    course_count = (await db.execute(select(func.count(Course.id)))).scalar() or 0
    question_count = (await db.execute(select(func.count(Question.id)))).scalar() or 0
    project_count = (await db.execute(select(func.count(Project.id)))).scalar() or 0
    post_count = (await db.execute(select(func.count(Post.id)))).scalar() or 0

    return api_response(data={
        "users": user_count, "courses": course_count,
        "questions": question_count, "projects": project_count,
        "posts": post_count,
    })
