from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.database import Base


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    content = Column(Text)
    timestamp_seconds = Column(Integer, default=0)  # video position in seconds
    time_text = Column(String(20), default="00:00")  # formatted display: MM:SS or HH:MM:SS
    note_type = Column(String(20), default="重点")  # 重点 / 疑问 / 总结 / 代码 / 其他
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
