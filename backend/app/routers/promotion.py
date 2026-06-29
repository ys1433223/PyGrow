"""
Promotion exam router — status, start, submit, result.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.promotion import PromotionExam
from app.schemas.common import api_response
from app.services.promotion_service import (
    select_promotion_questions,
    grade_promotion_exam,
    get_learned_scope,
    _get_stage_for_rank,
)
from app.services.gamification import calc_rank_progress, get_rank_exp_limit, get_next_rank, MAJOR_LEVELS

router = APIRouter(prefix="/api/promotion", tags=["promotion"])


@router.get("/status")
async def get_promotion_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return promotion exam eligibility and progress."""
    current_rank = user.current_rank or "萌新小白"
    rank_exp_limit = get_rank_exp_limit(current_rank)
    current_exp = user.current_exp or 0
    is_exp_full = current_exp >= rank_exp_limit
    next_rank = get_next_rank(current_rank)
    can_take = is_exp_full and next_rank is not None

    # Check if there's an in-progress exam
    result = await db.execute(
        select(PromotionExam).where(
            PromotionExam.user_id == user.id,
            PromotionExam.status == "in_progress",
        ).order_by(PromotionExam.created_at.desc()).limit(1)
    )
    in_progress = result.scalar_one_or_none()

    # Get latest completed exam for reference
    result = await db.execute(
        select(PromotionExam).where(
            PromotionExam.user_id == user.id,
            PromotionExam.status == "completed",
        ).order_by(PromotionExam.created_at.desc()).limit(1)
    )
    last_exam = result.scalar_one_or_none()

    # Get learned scope summary
    scope = await get_learned_scope(db, user.id)

    return api_response(data={
        "can_take": can_take,
        "current_rank": current_rank,
        "current_exp": current_exp,
        "rank_exp_limit": rank_exp_limit,
        "next_rank": next_rank,
        "exp_full": is_exp_full,
        "major_level": calc_rank_progress(current_rank, current_exp, user.total_exp or 0).get("major_level", "初级"),
        "has_in_progress": in_progress is not None,
        "in_progress_id": in_progress.id if in_progress else None,
        "last_exam": {
            "id": last_exam.id,
            "score": last_exam.score,
            "passed": last_exam.passed,
            "created_at": str(last_exam.completed_at or last_exam.created_at),
        } if last_exam else None,
        "learned_tags_count": len(scope.get("learned_tags", set())),
        "weak_tags_count": len(scope.get("weak_tags", {})),
    })


@router.post("/start")
async def start_promotion_exam(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new promotion exam paper."""
    # Check eligibility
    current_rank = user.current_rank or "萌新小白"
    rank_exp_limit = get_rank_exp_limit(current_rank)
    is_exp_full = (user.current_exp or 0) >= rank_exp_limit
    next_rank = get_next_rank(current_rank)

    if not is_exp_full or next_rank is None:
        return api_response(code=400, message="经验值未满或已是最高段位，无法参加晋级赛")

    # Check no in-progress exam
    result = await db.execute(
        select(PromotionExam).where(
            PromotionExam.user_id == user.id,
            PromotionExam.status == "in_progress",
        )
    )
    if result.scalar_one_or_none():
        return api_response(code=400, message="已有进行中的晋级赛，请先完成")

    # Generate questions
    paper = await select_promotion_questions(db, user.id, count=10)

    if not paper["questions"]:
        return api_response(code=500, message="无法生成晋级赛题目，请稍后再试")

    # Create exam record
    stage = _get_stage_for_rank(current_rank)
    exam = PromotionExam(
        user_id=user.id,
        rank_at_time=current_rank,
        major_level=stage,
        questions=paper["questions"],
        status="in_progress",
    )
    db.add(exam)
    await db.commit()
    await db.refresh(exam)

    # Return without answers for the student
    questions_for_student = []
    for q in paper["questions"]:
        questions_for_student.append({
            "index": q["index"],
            "question_id": q["question_id"],
            "title": q["title"],
            "content": q["content"],
            "type": q["type"],
            "options": q["options"],
            "difficulty": q.get("difficulty", "medium"),
            "score": q.get("score", 5),
            "source": q.get("source", "question_bank"),
            "reason": q.get("reason", ""),
            "knowledge_tag": q.get("knowledge_tag", ""),
            "starter_code": q.get("starter_code"),
        })

    return api_response(data={
        "exam_id": exam.id,
        "questions": questions_for_student,
        "total": len(questions_for_student),
        "source_breakdown": paper.get("source_breakdown", {}),
        "time_limit_minutes": 30,
    })


@router.post("/submit")
async def submit_promotion_exam(
    answers: dict,  # {question_id: user_answer, ...}
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    exam_id: int = Query(..., description="Exam ID"),
):
    """Submit answers and get results."""
    result = await db.execute(
        select(PromotionExam).where(
            PromotionExam.id == exam_id,
            PromotionExam.user_id == user.id,
            PromotionExam.status == "in_progress",
        )
    )
    exam = result.scalar_one_or_none()
    if not exam:
        return api_response(code=404, message="晋级赛不存在或已完成")

    # Grade
    questions = exam.questions or []
    grade_result = grade_promotion_exam(questions, answers, exam)

    # Update exam record
    exam.answers = grade_result["graded_questions"]
    exam.score = grade_result["score"]
    exam.core_correct_rate = grade_result["core_correct_rate"]
    exam.passed = grade_result["passed"]
    exam.weakness_tags = grade_result["weakness_tags"]
    exam.feedback = grade_result["feedback"]
    exam.status = "completed"
    exam.completed_at = datetime.utcnow()

    # If passed → promote
    if grade_result["passed"]:
        next_rank = get_next_rank(exam.rank_at_time)
        if next_rank:
            user.current_rank = next_rank
            user.current_exp = 0
            user.rank_exp_limit = get_rank_exp_limit(next_rank)
            user.total_exp = (user.total_exp or 0) + 50  # Bonus EXP for passing

    await db.commit()

    # Prepare result (show correct answers after submission)
    result_questions = []
    for q in questions:
        result_questions.append({
            "index": q.get("index", 0),
            "question_id": q.get("question_id", q.get("id", "")),
            "title": q.get("title", ""),
            "content": q.get("content", ""),
            "type": q.get("type", ""),
            "options": q.get("options"),
            "correct_answer": q.get("answer", ""),
            "analysis": q.get("analysis", ""),
            "your_answer": answers.get(str(q.get("question_id", q.get("id", ""))), ""),
            "difficulty": q.get("difficulty", "medium"),
            "knowledge_tag": q.get("knowledge_tag", ""),
            "source": q.get("source", "question_bank"),
        })

    return api_response(data={
        "exam_id": exam.id,
        "passed": grade_result["passed"],
        "score": grade_result["score"],
        "core_correct_rate": grade_result["core_correct_rate"],
        "questions": result_questions,
        "weakness_tags": exam.weakness_tags,
        "feedback": exam.feedback,
        "new_rank": user.current_rank if grade_result["passed"] else None,
    })


@router.get("/result")
async def get_promotion_result(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    exam_id: int = Query(None, description="Specific exam ID, omit for latest"),
):
    """View promotion exam results and feedback."""
    if exam_id:
        result = await db.execute(
            select(PromotionExam).where(
                PromotionExam.id == exam_id,
                PromotionExam.user_id == user.id,
            )
        )
    else:
        result = await db.execute(
            select(PromotionExam).where(
                PromotionExam.user_id == user.id,
                PromotionExam.status == "completed",
            ).order_by(PromotionExam.created_at.desc()).limit(1)
        )
    exam = result.scalar_one_or_none()
    if not exam:
        return api_response(code=404, message="未找到晋级赛记录")

    return api_response(data={
        "exam_id": exam.id,
        "rank_at_time": exam.rank_at_time,
        "status": exam.status,
        "score": exam.score,
        "core_correct_rate": exam.core_correct_rate,
        "passed": exam.passed,
        "weakness_tags": exam.weakness_tags or [],
        "feedback": exam.feedback or [],
        "questions": [
            {
                "index": q.get("index", 0),
                "question_id": q.get("question_id", ""),
                "title": q.get("title", ""),
                "content": q.get("content", ""),
                "type": q.get("type", ""),
                "options": q.get("options"),
                "difficulty": q.get("difficulty", "medium"),
                "knowledge_tag": q.get("knowledge_tag", ""),
                "source": q.get("source", "question_bank"),
                "is_correct": q.get("is_correct"),
                "analysis": q.get("analysis", ""),
            }
            for q in (exam.questions or [])
        ],
        "answers": [
            {"question_id": a.get("question_id", ""), "user_answer": a.get("user_answer", ""),
             "is_correct": a.get("is_correct"), "correct_answer": a.get("correct_answer", "")}
            for a in (exam.answers or [])
        ],
        "created_at": str(exam.created_at),
        "completed_at": str(exam.completed_at) if exam.completed_at else None,
        "promoted_to": get_next_rank(exam.rank_at_time) if exam.passed else None,
    })
