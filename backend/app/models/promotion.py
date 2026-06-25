from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, func
from app.database import Base


class PromotionExam(Base):
    __tablename__ = "promotion_exams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rank_at_time = Column(String(50), nullable=False)        # e.g. "萌新小白"
    major_level = Column(String(50))                          # 初级/中级/高级
    questions = Column(JSON, nullable=False)                   # [{id, question_id, source, ...}]
    answers = Column(JSON)                                     # [{question_id, user_answer, is_correct}]
    score = Column(Float, default=0)                           # total score 0-100
    core_correct_rate = Column(Float, default=0)              # core question accuracy
    passed = Column(Boolean, default=False)
    weakness_tags = Column(JSON)                               # failed knowledge tags
    feedback = Column(JSON)                                    # [{tag, suggestion, chapter}]
    status = Column(String(20), default="in_progress")        # in_progress / completed
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
