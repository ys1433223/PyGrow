from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.course import Lesson
from app.models.note import Note
from app.schemas.common import api_response

router = APIRouter()


class NoteCreate(BaseModel):
    lesson_id: int
    course_id: int
    content: str
    timestamp_seconds: int = 0


@router.get("/course/{course_id}")
async def list_notes_by_course(
    course_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all notes for a course."""
    result = await db.execute(
        select(Note)
        .where(Note.user_id == user.id, Note.course_id == course_id)
        .order_by(Note.created_at.desc())
    )
    notes = result.scalars().all()
    return api_response(data=[
        {
            "id": n.id, "lesson_id": n.lesson_id, "course_id": n.course_id,
            "content": n.content, "timestamp_seconds": n.timestamp_seconds,
            "created_at": str(n.created_at),
        }
        for n in notes
    ])


@router.post("")
async def create_note(
    req: NoteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a timestamp note."""
    # Verify lesson exists
    lesson = (await db.execute(select(Lesson).where(Lesson.id == req.lesson_id))).scalar_one_or_none()
    if not lesson:
        return api_response(404, "课时不存在")

    note = Note(
        user_id=user.id,
        course_id=req.course_id,
        lesson_id=req.lesson_id,
        content=req.content,
        timestamp_seconds=req.timestamp_seconds,
    )
    db.add(note)
    await db.commit()

    return api_response(data={
        "id": note.id,
        "lesson_id": note.lesson_id,
        "timestamp_seconds": note.timestamp_seconds,
        "content": note.content,
        "created_at": str(note.created_at),
    })


@router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a note."""
    note = (await db.execute(select(Note).where(Note.id == note_id, Note.user_id == user.id))).scalar_one_or_none()
    if not note:
        return api_response(404, "笔记不存在")

    await db.delete(note)
    await db.commit()
    return api_response(data={"message": "已删除"})
