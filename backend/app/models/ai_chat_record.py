from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.database import Base


class AIChatRecord(Base):
    __tablename__ = "ai_chat_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question = Column(Text, nullable=False)
    code = Column(Text)
    answer = Column(Text)
    type = Column(String(50))  # explain / debug / ask / suggestion
    created_at = Column(DateTime, server_default=func.now())
