from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, func
from app.database import Base


class CodeSubmission(Base):
    __tablename__ = "code_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    code = Column(Text, nullable=False)
    language = Column(String(50), default="python")
    run_result = Column(Text)
    is_correct = Column(Boolean)
    score = Column(Float, default=0)
    created_at = Column(DateTime, server_default=func.now())
