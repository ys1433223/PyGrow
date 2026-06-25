from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, func
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, index=True)
    stage = Column(String(50))  # 初级/中级/高级
    chapter = Column(Integer)
    knowledge_tags = Column(JSON)  # list of strings
    difficulty = Column(String(50))  # easy/medium/hard
    project_title = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)  # alias for project_title
    task_description = Column(Text)
    description = Column(Text)  # alias for task_description
    requirements = Column(JSON)  # list of requirement strings
    submit_type = Column(String(50), default="code")  # code / text / file / mixed
    rubric = Column(JSON)  # scoring rubric dimensions
    max_score = Column(Integer, default=100)
    ai_review_enabled = Column(Integer, default=1)
    reward_exp = Column(Integer, default=50)
    reward_points = Column(Integer, default=30)
    icon = Column(String(100))
    cover_color = Column(String(100))
    content = Column(Text)  # legacy
    level = Column(String(50))  # legacy
    category = Column(String(100))  # legacy
    created_at = Column(DateTime, server_default=func.now())


class ProjectSubmission(Base):
    __tablename__ = "project_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    code = Column(Text)
    text = Column(Text)
    file_url = Column(String(500))
    screenshot_url = Column(String(500))
    status = Column(String(50), default="submitted")  # submitted / reviewed

    # AI review results
    total_score = Column(Float)
    level = Column(String(50))  # 优秀/良好/达标/需修改
    dimension_scores = Column(JSON)  # {功能完整性: n, 代码正确性: n, ...}
    strengths = Column(JSON)  # list of strings
    problems = Column(JSON)  # list of strings
    suggestions = Column(JSON)  # list of strings
    related_knowledge = Column(JSON)  # list of strings

    # Gamification
    experience_gained = Column(Integer, default=0)
    points_gained = Column(Integer, default=0)
    hints_used = Column(Integer, default=0)

    submitted_at = Column(DateTime, server_default=func.now())
