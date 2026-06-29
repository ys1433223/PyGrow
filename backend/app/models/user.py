from sqlalchemy import Column, Integer, String, DateTime, Date, func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    avatar = Column(String(500), default="https://api.dicebear.com/7.x/avataaars/svg?seed=User")
    nickname = Column(String(50))
    email = Column(String(100))
    # Legacy level system (kept for backward compat)
    level = Column(String(50), default="萌新小白")
    experience = Column(Integer, default=0)
    points = Column(Integer, default=0)
    # New rank system with EXP caps
    current_rank = Column(String(50), default="萌新小白")
    current_exp = Column(Integer, default=0)
    rank_exp_limit = Column(Integer, default=100)
    total_exp = Column(Integer, default=0)
    can_promotion_test = Column(Integer, default=0)  # 0=no, 1=yes
    # Cookie currency for pet system
    cookies = Column(Integer, default=0)
    # Daily cookie tracking (resets each day, cap 30)
    daily_cookies = Column(Integer, default=0)
    daily_cookies_date = Column(Date)
    # Daily EXP tracking (resets each day)
    daily_exp = Column(Integer, default=0)
    daily_exp_date = Column(Date)
    # Placement assessment flag (0=not taken, 1=completed, -1=skipped)
    is_assessed = Column(Integer, default=0)
    # Admin
    is_admin = Column(Integer, default=0)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
