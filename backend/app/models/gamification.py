from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Date, ForeignKey, JSON, func
from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, index=True)  # Global unique ID from parsed data
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # single_choice, multiple_choice, judge, fill_blank, short_answer, code
    options = Column(JSON)
    answer = Column(Text)
    analysis = Column(Text)
    knowledge_point = Column(String(100))
    knowledge_tag = Column(String(100))
    knowledge_type = Column(String(50))  # concept/comparison/application/code/debug
    difficulty = Column(String(50))
    level = Column(String(50))
    stage = Column(String(50))  # 初级/中级/高级
    chapter = Column(String(100))
    chapter_num = Column(Integer)
    test_cases = Column(JSON)
    starter_code = Column(Text)
    score = Column(Integer, default=5)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PracticeRecord(Base):
    __tablename__ = "practice_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_answer = Column(Text)
    is_correct = Column(Boolean)
    score = Column(Float, default=0)
    hints_used = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon_url = Column(String(255))
    condition_type = Column(String(50))
    condition_value = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime, server_default=func.now())


class DailyTask(Base):
    __tablename__ = "daily_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    task_type = Column(String(50))
    reward_exp = Column(Integer, default=0)
    reward_points = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class UserDailyTask(Base):
    __tablename__ = "user_daily_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("daily_tasks.id"), nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    date = Column(Date)
