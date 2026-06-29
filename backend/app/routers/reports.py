from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, distinct

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.course import CourseProgress, Lesson
from app.models.gamification import PracticeRecord, Question
from app.models.community import Post
from app.models.favorite import Favorite
from app.models.project import ProjectSubmission
from app.schemas.common import api_response
from app.services.gamification import calc_rank_progress

router = APIRouter()


@router.get("/summary")
async def get_report_summary(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Learning report summary."""
    # Course count
    course_result = await db.execute(
        select(CourseProgress).where(CourseProgress.user_id == user.id)
    )
    progress_list = course_result.scalars().all()
    completed_courses = sum(1 for p in progress_list if p.is_completed)
    in_progress = len(progress_list) - completed_courses

    # Practice stats
    total_result = await db.execute(
        select(func.count()).select_from(PracticeRecord).where(PracticeRecord.user_id == user.id)
    )
    total_practice = total_result.scalar() or 0

    correct_result = await db.execute(
        select(func.count()).select_from(PracticeRecord).where(
            PracticeRecord.user_id == user.id, PracticeRecord.is_correct == True
        )
    )
    correct_count = correct_result.scalar() or 0
    wrong_count = total_practice - correct_count
    accuracy = round(correct_count / total_practice * 100) if total_practice > 0 else 0

    rank_info = calc_rank_progress(
        user.current_rank or "萌新小白",
        user.current_exp or 0,
        user.total_exp or 0,
    )

    return api_response(data={
        "completed_courses": completed_courses,
        "in_progress_courses": in_progress,
        "total_practice": total_practice,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "accuracy": accuracy,
        "level": rank_info["current_rank"],
        "current_xp": rank_info["current_exp"],
        "next_level_xp": rank_info["rank_exp_limit"],
        "progress_percent": rank_info["progress_percent"],
        "major_level": rank_info["major_level"],
        "experience": rank_info["total_exp"],
    })


@router.get("/knowledge-points")
async def get_knowledge_report(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Knowledge point mastery data for chart display."""
    result = await db.execute(
        select(
            Question.knowledge_point,
            func.count().label("total"),
            func.sum(PracticeRecord.is_correct).label("correct"),
        )
        .join(PracticeRecord, PracticeRecord.question_id == Question.id)
        .where(PracticeRecord.user_id == user.id)
        .group_by(Question.knowledge_point)
    )
    rows = result.all()

    knowledge = []
    for kp, total, correct in rows:
        pct = round(correct / total * 100) if total else 0
        knowledge.append({
            "knowledge_point": kp,
            "total": total,
            "correct": correct or 0,
            "mastery_percent": pct,
        })

    return api_response(data=knowledge)


@router.get("/radar-data")
async def get_radar_data(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Return 6-dimension radar chart data computed from existing records.

    Dimensions (each 0–100):
      1. 学习投入度 — study time proxy + login days
      2. 课程掌握度 — course progress + completed chapters
      3. 练习表现   — answer accuracy + volume
      4. 编程实践能力 — code runs (unavailable → 0) + project submissions
      5. 薄弱修复能力 — wrong-question re-practice + wrong→correct conversions
      6. 学习自主性 — total practice + favorites + community posts
    """

    # --- Reusable aggregates -------------------------------------------------
    total_practice_q = select(func.count()).select_from(PracticeRecord).where(
        PracticeRecord.user_id == user.id
    )
    total_practice = (await db.execute(total_practice_q)).scalar() or 0

    correct_q = select(func.count()).select_from(PracticeRecord).where(
        PracticeRecord.user_id == user.id, PracticeRecord.is_correct == True
    )
    correct_count = (await db.execute(correct_q)).scalar() or 0

    # ----- 1. 学习投入度 ------------------------------------------------
    # Study-time proxy: total_practice × 3 min per question
    study_minutes = total_practice * 3
    study_score = min(study_minutes / 300 * 100, 100)

    # Login days: distinct dates from PracticeRecord
    login_days_q = select(func.count(distinct(func.date(PracticeRecord.created_at)))).where(
        PracticeRecord.user_id == user.id
    )
    login_days = (await db.execute(login_days_q)).scalar() or 0
    login_score = min(login_days / 7 * 100, 100)

    engagement = round(study_score * 0.6 + login_score * 0.4)

    # ----- 2. 课程掌握度 ------------------------------------------------
    progress_q = select(
        func.avg(CourseProgress.progress_percent),
        func.count()
    ).where(CourseProgress.user_id == user.id)
    avg_progress, course_count = (await db.execute(progress_q)).one()
    course_progress_score = float(avg_progress or 0)

    completed_q = select(func.count()).where(
        CourseProgress.user_id == user.id, CourseProgress.is_completed == True
    )
    completed_chapters = (await db.execute(completed_q)).scalar() or 0
    chapter_score = min(completed_chapters / 10 * 100, 100)

    mastery = round(course_progress_score * 0.7 + chapter_score * 0.3)

    # ----- 3. 练习表现 --------------------------------------------------
    accuracy = round(correct_count / total_practice * 100) if total_practice > 0 else 0
    volume_score = min(total_practice / 50 * 100, 100)

    practice = round(accuracy * 0.7 + volume_score * 0.3)

    # ----- 4. 编程实践能力 ----------------------------------------------
    # Code runs: not tracked — fallback to 0
    code_run_score = 0

    project_count_q = select(func.count()).select_from(ProjectSubmission).where(
        ProjectSubmission.user_id == user.id
    )
    project_count = (await db.execute(project_count_q)).scalar() or 0
    project_score = min(project_count / 3 * 100, 100)

    coding = round(code_run_score * 0.5 + project_score * 0.5)

    # ----- 5. 薄弱修复能力 ----------------------------------------------
    # Wrong-then-retry: questions attempted more than once where at least one answer was wrong
    re_practice_q = select(
        PracticeRecord.question_id,
        func.count().label("attempts"),
        func.sum(case((PracticeRecord.is_correct == True, 1), else_=0)).label("correct"),
        func.sum(case((PracticeRecord.is_correct == False, 1), else_=0)).label("wrong")
    ).where(PracticeRecord.user_id == user.id).group_by(PracticeRecord.question_id).having(
        func.count() > 1
    )
    re_practice_rows = (await db.execute(re_practice_q)).all()

    # 错题复练次数: sum of (attempts - 1) for questions that were ever wrong
    retry_count = 0
    # 错题重新做对数量: count of questions that were wrong then later correct
    fixed_count = 0
    for qid, att, cor, wro in re_practice_rows:
        if (wro or 0) > 0:
            retry_count += (att - 1)  # re-attempts beyond the first
            if (cor or 0) > 0:
                fixed_count += 1

    retry_score = min(retry_count / 20 * 100, 100)
    fixed_score = min(fixed_count / 10 * 100, 100)

    weakness = round(retry_score * 0.5 + fixed_score * 0.5)

    # ----- 6. 学习自主性 ------------------------------------------------
    self_practice_score = min(total_practice / 20 * 100, 100)

    fav_count_q = select(func.count()).select_from(Favorite).where(Favorite.user_id == user.id)
    fav_count = (await db.execute(fav_count_q)).scalar() or 0
    fav_score = min(fav_count / 10 * 100, 100)

    post_count_q = select(func.count()).select_from(Post).where(Post.user_id == user.id)
    post_count = (await db.execute(post_count_q)).scalar() or 0
    social_score = min(post_count / 5 * 100, 100)

    autonomy = round(self_practice_score * 0.4 + fav_score * 0.3 + social_score * 0.3)

    # --- Build response -------------------------------------------------------
    dimensions = [
        {
            "key": "engagement",
            "name": "学习投入度",
            "score": engagement,
            "sources": ["累计学习时长", "登录天数"],
        },
        {
            "key": "mastery",
            "name": "课程掌握度",
            "score": mastery,
            "sources": ["课程完成进度", "已完成章节数"],
        },
        {
            "key": "practice",
            "name": "练习表现",
            "score": practice,
            "sources": ["答题正确率", "答题数量"],
        },
        {
            "key": "coding",
            "name": "编程实践能力",
            "score": coding,
            "sources": ["在线编程运行次数", "综合项目完成数"],
        },
        {
            "key": "weakness",
            "name": "薄弱修复能力",
            "score": weakness,
            "sources": ["错题复练次数", "错题重新做对数量"],
        },
        {
            "key": "autonomy",
            "name": "学习自主性",
            "score": autonomy,
            "sources": ["自主练习次数", "收藏数量", "社区发帖数"],
        },
    ]

    return api_response(data={
        "dimensions": dimensions,
        "description": "雷达图根据学习时长、课程进度、练习记录、代码实践、错题复练和自主学习行为综合生成。",
    })
