import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.deps import get_current_user
from app.models.ai_note import AINoteTask, AINote
from app.models.user import User
from app.schemas.common import api_response
from app.services.ai_note_service import STATUS_MESSAGES, run_ai_note_pipeline
from app.services.download_queue import get_queue_position

router = APIRouter()


@router.get("/courses/{course_id}/ai-notes")
async def get_ai_notes(
    course_id: int,
    lesson_id: int | None = None,
    bvid: str | None = None,
    bilibili_page: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Check if a course (or specific lesson) already has AI notes."""
    stmt = select(AINote).where(AINote.course_id == course_id)
    if lesson_id is not None:
        stmt = stmt.where(AINote.lesson_id == lesson_id)
    elif bvid and bilibili_page is not None:
        stmt = stmt.where(AINote.bvid == bvid, AINote.bilibili_page == bilibili_page)
    stmt = stmt.order_by(AINote.created_at.desc())
    result = await db.execute(stmt)
    notes = result.scalars().all()

    if lesson_id is not None or (bvid and bilibili_page is not None):
        # Specific lesson — return the first match (should be at most one)
        note = notes[0] if notes else None
        if note:
            return api_response(data={
                "has_note": True,
                "note_id": note.id,
                "lesson_id": note.lesson_id,
                "summary": note.summary,
                "notes": note.notes or [],
                "highlights": note.highlights or [],
                "transcript": note.transcript or "",
                "errors": note.errors or [],
                "suggestions": note.suggestions or [],
                "source_type": note.source_type,
                "created_at": str(note.created_at),
            })
        return api_response(data={"has_note": False})

    # No lesson_id or bvid+page — return all notes for this course
    if not notes:
        return api_response(data={"has_note": False, "notes": []})
    return api_response(data={
        "has_note": True,
        "notes": [
            {
                "note_id": n.id,
                "lesson_id": n.lesson_id,
                "summary": n.summary,
                "notes": n.notes or [],
                "highlights": n.highlights or [],
                "transcript": n.transcript or "",
                "errors": n.errors or [],
                "suggestions": n.suggestions or [],
                "source_type": n.source_type,
                "created_at": str(n.created_at),
            }
            for n in notes
        ],
    })


@router.post("/courses/{course_id}/ai-notes/generate")
async def generate_ai_notes(
    course_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lesson_id: int | None = None,
    bvid: str | None = None,
    bilibili_page: int | None = None,
):
    """Start an AI note generation task for a specific lesson. Returns immediately with task_id."""
    # 1. Check if notes already exist — by lesson_id first, then by bvid+page
    if lesson_id is not None:
        stmt = select(AINote).where(AINote.course_id == course_id, AINote.lesson_id == lesson_id)
        stmt = stmt.order_by(AINote.created_at.desc()).limit(1)
        existing = await db.execute(stmt)
        note = existing.scalars().first()
        if note:
            return api_response(data={
                "task_id": note.task_id,
                "status": "completed",
                "note": {
                    "lesson_id": note.lesson_id,
                    "summary": note.summary,
                    "notes": note.notes or [],
                    "highlights": note.highlights or [],
                    "transcript": note.transcript or "",
                    "errors": note.errors or [],
                    "suggestions": note.suggestions or [],
                    "source_type": note.source_type,
                },
            })
    elif bvid and bilibili_page is not None:
        stmt = select(AINote).where(AINote.course_id == course_id, AINote.bvid == bvid, AINote.bilibili_page == bilibili_page)
        stmt = stmt.order_by(AINote.created_at.desc()).limit(1)
        existing = await db.execute(stmt)
        note = existing.scalars().first()
        if note:
            return api_response(data={
                "task_id": note.task_id,
                "status": "completed",
                "note": {
                    "lesson_id": note.lesson_id,
                    "summary": note.summary,
                    "notes": note.notes or [],
                    "highlights": note.highlights or [],
                    "transcript": note.transcript or "",
                    "errors": note.errors or [],
                    "suggestions": note.suggestions or [],
                    "source_type": note.source_type,
                },
            })

    # 2. Check if a task is already in progress for this lesson
    active_statuses = ["not_started", "queued", "downloading", "extracting_audio", "transcribing", "summarizing"]
    task_stmt = select(AINoteTask).where(
        AINoteTask.course_id == course_id,
        AINoteTask.status.in_(active_statuses),
    )
    if lesson_id is not None:
        task_stmt = task_stmt.where(AINoteTask.lesson_id == lesson_id)
    elif bvid and bilibili_page is not None:
        task_stmt = task_stmt.where(AINoteTask.bvid == bvid, AINoteTask.bilibili_page == bilibili_page)
    task_stmt = task_stmt.order_by(AINoteTask.created_at.desc()).limit(1)
    active_task_result = await db.execute(task_stmt)
    active_task = active_task_result.scalars().first()
    if active_task:
        return api_response(data={
            "task_id": active_task.id,
            "status": active_task.status,
            "message": STATUS_MESSAGES.get(active_task.status, active_task.status),
        })

    # 3. Create new task
    task = AINoteTask(
        course_id=course_id,
        lesson_id=lesson_id,
        bvid=bvid,
        bilibili_page=bilibili_page,
        status="not_started",
        progress=0,
        message=STATUS_MESSAGES["not_started"],
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # 4. Start background pipeline (pass bvid/page overrides for local-data scenarios)
    asyncio.create_task(run_ai_note_pipeline(task.id, course_id, lesson_id, bvid, bilibili_page))

    return api_response(data={
        "task_id": task.id,
        "status": task.status,
        "message": task.message,
    })


@router.get("/ai-note-tasks/{task_id}/status")
async def get_task_status(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Poll the status of an AI note generation task."""
    task = await db.get(AINoteTask, task_id)
    if not task:
        return api_response(404, "任务不存在")

    return api_response(data={
        "task_id": task.id,
        "course_id": task.course_id,
        "status": task.status,
        "progress": task.progress,
        "message": task.message,
        "error_message": task.error_message,
        "queue_position": get_queue_position(task_id),
    })


@router.get("/ai-note-tasks/{task_id}/result")
async def get_task_result(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get the AI note result after a task completes."""
    task = await db.get(AINoteTask, task_id)
    if not task:
        return api_response(404, "任务不存在")
    if task.status == "failed":
        return api_response(500, task.error_message or "任务执行失败")
    if task.status != "completed":
        return api_response(data={
            "ready": False,
            "status": task.status,
            "message": STATUS_MESSAGES.get(task.status, task.status),
        })

    result = await db.execute(
        select(AINote).where(AINote.task_id == task_id).limit(1)
    )
    note = result.scalars().first()
    if not note:
        return api_response(404, "笔记数据不存在")

    return api_response(data={
        "ready": True,
        "summary": note.summary,
        "notes": note.notes or [],
        "highlights": note.highlights or [],
        "transcript": note.transcript or "",
        "errors": note.errors or [],
        "suggestions": note.suggestions or [],
        "source_type": note.source_type,
    })
