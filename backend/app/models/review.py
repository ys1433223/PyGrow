from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.database import Base


class CourseReview(Base):
    __tablename__ = "course_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(String(50), nullable=False, comment="初级/中级/高级")
    rating = Column(Integer, nullable=False, comment="1-5 stars")
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
