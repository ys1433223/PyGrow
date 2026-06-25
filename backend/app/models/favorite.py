from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.database import Base


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_type = Column(String(20), nullable=False, comment="course / question")
    item_id = Column(String(100), nullable=False, comment="level-chapter for course, question id for question")
    title = Column(String(255), comment="display title for quick reference")
    created_at = Column(DateTime, server_default=func.now())
