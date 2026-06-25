from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.project import Project, ProjectSubmission
from app.schemas.common import api_response
from app.services.gamification import calc_level, award_badge_if_earned, reset_daily_exp_if_new_day, get_rank_exp_limit
from app.services.project_review_service import review_project, calc_project_xp
from app.services.pet_service import award_cookies

router = APIRouter()


class ProjectSubmitRequest(BaseModel):
    code: str = ""
    text: str = ""
    file_url: str = ""
    screenshot_url: str = ""
    hints_used: int = 0


class ProjectInfo(BaseModel):
    project_title: str = ""
    task_description: str = ""
    requirements: List[str] = []
    knowledge_tags: List[str] = []
    difficulty: str = "medium"
    max_score: int = 100


@router.get("")
async def list_projects(
    stage: str = None,
    difficulty: str = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all projects, optionally filtered by stage and difficulty."""
    q = select(Project)
    if stage:
        q = q.where(Project.stage == stage)
    if difficulty:
        q = q.where(Project.difficulty == difficulty)
    q = q.order_by(Project.stage, Project.chapter, Project.id)
    result = await db.execute(q)
    projects = result.scalars().all()

    # Get best score per project for this user
    items = []
    for p in projects:
        best_result = await db.execute(
            select(func.max(ProjectSubmission.total_score))
            .where(ProjectSubmission.user_id == user.id, ProjectSubmission.project_id == p.id)
        )
        best_score = best_result.scalar()

        items.append({
            "id": p.id,
            "project_id": p.project_id or p.id,
            "title": p.project_title or p.title,
            "stage": p.stage,
            "chapter": p.chapter,
            "knowledge_tags": p.knowledge_tags or [],
            "difficulty": p.difficulty,
            "task_description": p.task_description or p.description,
            "requirements": p.requirements or [],
            "submit_type": p.submit_type or "code",
            "max_score": p.max_score or 100,
            "ai_review_enabled": bool(p.ai_review_enabled),
            "reward_exp": p.reward_exp or 50,
            "reward_points": p.reward_points or 30,
            "best_score": best_score,
        })

    return api_response(data=items)


@router.get("/{project_id}")
async def get_project_detail(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return full project detail with user's submission history."""
    result = await db.execute(select(Project).where(Project.project_id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        return api_response(404, "项目不存在")

    # Get submission history
    sub_result = await db.execute(
        select(ProjectSubmission)
        .where(ProjectSubmission.user_id == user.id, ProjectSubmission.project_id == project.id)
        .order_by(desc(ProjectSubmission.submitted_at))
    )
    submissions = sub_result.scalars().all()

    return api_response(data={
        "id": project.id,
        "project_id": project.project_id or project.id,
        "title": project.project_title or project.title,
        "stage": project.stage,
        "chapter": project.chapter,
        "knowledge_tags": project.knowledge_tags or [],
        "difficulty": project.difficulty,
        "task_description": project.task_description or project.description,
        "requirements": project.requirements or [],
        "submit_type": project.submit_type or "code",
        "rubric": project.rubric or {},
        "max_score": project.max_score or 100,
        "ai_review_enabled": bool(project.ai_review_enabled),
        "reward_exp": project.reward_exp or 50,
        "submissions": [
            {
                "id": s.id, "code": s.code, "text": s.text,
                "file_url": s.file_url, "screenshot_url": s.screenshot_url,
                "status": s.status,
                "total_score": s.total_score, "level": s.level,
                "dimension_scores": s.dimension_scores,
                "strengths": s.strengths, "problems": s.problems,
                "suggestions": s.suggestions,
                "related_knowledge": s.related_knowledge,
                "experience_gained": s.experience_gained,
                "hints_used": s.hints_used,
                "submitted_at": str(s.submitted_at),
            }
            for s in submissions
        ],
    })


@router.post("/{project_id}/submit")
async def submit_project_for_review(
    project_id: int,
    req: ProjectSubmitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit project for AI review. Returns score, dimensions, strengths, problems, suggestions."""
    result = await db.execute(select(Project).where(Project.project_id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        return api_response(404, "项目不存在")

    # Get best previous score for anti-farming
    best_result = await db.execute(
        select(func.max(ProjectSubmission.total_score))
        .where(ProjectSubmission.user_id == user.id, ProjectSubmission.project_id == project.id)
    )
    best_previous = best_result.scalar() or 0

    # Call AI review
    review = await review_project(
        project_title=project.project_title or project.title or "",
        task_description=project.task_description or project.description or "",
        requirements=project.requirements or [],
        knowledge_tags=project.knowledge_tags or [],
        difficulty=project.difficulty or "medium",
        rubric=project.rubric,
        code=req.code,
        text=req.text,
        hints_used=req.hints_used,
    )

    # Calculate XP
    xp_info = calc_project_xp(
        difficulty=project.difficulty or "medium",
        ai_score=review["total_score"],
        hints_used=req.hints_used,
        best_previous_score=int(best_previous),
    )

    # Save submission
    sub = ProjectSubmission(
        user_id=user.id,
        project_id=project.id,
        code=req.code,
        text=req.text,
        file_url=req.file_url,
        screenshot_url=req.screenshot_url,
        status="reviewed",
        total_score=review["total_score"],
        level=review["level"],
        dimension_scores=review["dimension_scores"],
        strengths=review["strengths"],
        problems=review["problems"],
        suggestions=review["suggestions"],
        related_knowledge=review["related_knowledge"],
        experience_gained=xp_info["experience_gained"],
        points_gained=xp_info["experience_gained"],
        hints_used=req.hints_used,
    )
    db.add(sub)

    # Calculate cookie rewards based on score (10 for >=90, 5 for 75-89)
    cookie_reward = 0
    if review["total_score"] >= 90:
        cookie_reward = await award_cookies(db, user, 10, "project", f"综合项目评分 {review['total_score']} 分（优秀），获得 10 个饼干")
        await award_badge_if_earned(db, user.id, "project_excellent", 1)
    elif review["total_score"] >= 75:
        cookie_reward = await award_cookies(db, user, 5, "project", f"综合项目评分 {review['total_score']} 分（良好），获得 5 个饼干")

    # Award XP/points if earned
    if xp_info["experience_gained"] > 0:
        reset_daily_exp_if_new_day(user)
        user.experience += xp_info["experience_gained"]
        user.points += xp_info["experience_gained"]
        user.current_exp += xp_info["experience_gained"]
        user.total_exp += xp_info["experience_gained"]
        user.daily_exp = (user.daily_exp or 0) + xp_info["experience_gained"]

        old_rank = user.current_rank
        user.level = calc_level(user.total_exp)
        user.current_rank = calc_level(user.total_exp)
        if user.current_rank != old_rank:
            user.can_promotion_test = 0
            user.current_exp = 0
            user.rank_exp_limit = get_rank_exp_limit(user.current_rank)
            await award_badge_if_earned(db, user.id, "level_reach", user.total_exp)
        elif user.current_exp >= (user.rank_exp_limit or 100):
            user.can_promotion_test = 1

    # Count submissions for badge
    cnt_result = await db.execute(
        select(func.count()).select_from(ProjectSubmission).where(
            ProjectSubmission.user_id == user.id,
        )
    )
    sub_count = cnt_result.scalar() or 0
    await award_badge_if_earned(db, user.id, "project_count", sub_count)

    await db.commit()

    return api_response(data={
        "submission_id": sub.id,
        "status": "reviewed",
        "total_score": review["total_score"],
        "level": review["level"],
        "dimension_scores": review["dimension_scores"],
        "strengths": review["strengths"],
        "problems": review["problems"],
        "suggestions": review["suggestions"],
        "related_knowledge": review["related_knowledge"],
        "cookie_reward": cookie_reward,
        "cookies": user.cookies,
        "current_rank": user.current_rank,
        "current_exp": user.current_exp,
        "rank_exp_limit": user.rank_exp_limit,
        **xp_info,
        "new_level": user.level,
        "new_experience": user.experience,
    })


@router.post("/submit")
async def submit_project_legacy(
    req: ProjectSubmitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Legacy endpoint — delegates to the new review flow using project_id from request body."""
    # Extract project_id from a field that might be in the body
    # For backward compat with old frontend
    return api_response(400, "请使用 POST /api/projects/{project_id}/submit 提交项目")
