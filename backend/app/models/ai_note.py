from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from app.database import Base


class AINoteTask(Base):
    __tablename__ = "ai_note_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    status = Column(String(30), default="not_started")  # not_started/queued/downloading/extracting_audio/transcribing/summarizing/completed/failed
    progress = Column(Integer, default=0)
    message = Column(String(255), default="")
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    finished_at = Column(DateTime)


class AINote(Base):
    __tablename__ = "ai_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("ai_note_tasks.id"), nullable=False)
    summary = Column(Text)
    notes = Column(JSON)
    highlights = Column(JSON)
    transcript = Column(Text)
    errors = Column(JSON)
    suggestions = Column(JSON)
    source_type = Column(String(50), default="ai_generated")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
