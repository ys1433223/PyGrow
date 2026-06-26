import re
from datetime import datetime
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

# valid: HH:MM:SS, MM:SS, M:SS, H:MM:SS, HH:M:SS, etc.
TIME_RE = re.compile(r"^(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?$")


def parse_time_text(raw: str):
    """Parse a time string like '1:23', '01:23', '12:05', '1:02:33' into (seconds, normalized_text).
    Returns (None, error_message) on failure.
    """
    raw = raw.strip()
    m = TIME_RE.match(raw)
    if not m:
        return None, "请输入正确的时间格式，例如 03:20"
    h = int(m.group(1))
    min_ = int(m.group(2))
    sec = int(m.group(3)) if m.group(3) else 0

    if min_ >= 60 or sec >= 60:
        return None, "请输入正确的时间格式，例如 03:20"

    total = h * 3600 + min_ * 60 + sec

    if m.group(3):
        text = f"{h:02d}:{min_:02d}:{sec:02d}"
    else:
        text = f"{h:02d}:{min_:02d}"

    return {"seconds": total, "text": text}, None


class NoteCreate(BaseModel):
    lesson_id: int
    course_id: int
    content: str
    timestamp_seconds: int = 0
    time_text: str = "00:00"
    note_type: str = "重点"


class NoteUpdate(BaseModel):
    content: str = ""
    timestamp_seconds: int = 0
    time_text: str = "00:00"
    note_type: str = "重点"


def _note_to_dict(n: Note) -> dict:
    return {
        "id": n.id,
        "lesson_id": n.lesson_id,
        "course_id": n.course_id,
        "content": n.content,
        "timestamp_seconds": n.timestamp_seconds,
        "time_text": n.time_text or "00:00",
        "note_type": n.note_type or "重点",
        "created_at": str(n.created_at),
        "updated_at": str(n.updated_at) if n.updated_at else None,
    }


@router.get("/course/{course_id}")
async def list_notes_by_course(
    course_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all notes for a course, sorted by time ascending."""
    result = await db.execute(
        select(Note)
        .where(Note.user_id == user.id, Note.course_id == course_id)
        .order_by(Note.timestamp_seconds.asc())
    )
    notes = result.scalars().all()
    return api_response(data=[_note_to_dict(n) for n in notes])


@router.post("")
async def create_note(
    req: NoteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a timestamp note."""
    lesson = (await db.execute(select(Lesson).where(Lesson.id == req.lesson_id))).scalar_one_or_none()
    if not lesson:
        return api_response(404, "课时不存在")

    # Validate and normalise time
    parsed, err = parse_time_text(req.time_text)
    if err:
        return api_response(400, err)

    note = Note(
        user_id=user.id,
        course_id=req.course_id,
        lesson_id=req.lesson_id,
        content=req.content,
        timestamp_seconds=parsed["seconds"],
        time_text=parsed["text"],
        note_type=req.note_type or "重点",
    )
    db.add(note)
    await db.commit()

    return api_response(data=_note_to_dict(note))


@router.put("/{note_id}")
async def update_note(
    note_id: int,
    req: NoteUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit a timestamp note."""
    note = (
        await db.execute(
            select(Note).where(Note.id == note_id, Note.user_id == user.id)
        )
    ).scalar_one_or_none()
    if not note:
        return api_response(404, "笔记不存在")

    # Validate and normalise time
    parsed, err = parse_time_text(req.time_text)
    if err:
        return api_response(400, err)

    note.content = req.content
    note.timestamp_seconds = parsed["seconds"]
    note.time_text = parsed["text"]
    note.note_type = req.note_type or "重点"
    note.updated_at = datetime.utcnow()

    await db.commit()
    return api_response(data=_note_to_dict(note))


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
