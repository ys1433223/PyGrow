from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, func
from app.database import Base


class PetProfile(Base):
    __tablename__ = "pet_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    pet_name = Column(String(50), default="小Py")
    pet_type = Column(String(50), default="默认")
    status = Column(String(20), default="idle")  # idle / exploring / completed
    current_adventure_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PetAdventure(Base):
    __tablename__ = "pet_adventures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pet_id = Column(Integer, ForeignKey("pet_profiles.id"), nullable=False)
    adventure_location = Column(String(100), nullable=False)
    cost_cookies = Column(Integer, default=3)
    status = Column(String(20), default="exploring")  # exploring / completed / claimed
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    reward_type = Column(String(50), nullable=True)
    reward_value = Column(Integer, nullable=True)
    reward_description = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PetCookieRecord(Base):
    __tablename__ = "pet_cookie_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_type = Column(String(50), nullable=False)
    # daily_practice / question / code / project / promotion / signin / daily_task / adventure_cost
    cookies = Column(Integer, nullable=False, default=0)  # positive = earn, negative = spend
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class PetReward(Base):
    __tablename__ = "pet_rewards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    adventure_id = Column(Integer, ForeignKey("pet_adventures.id"), nullable=True)
    reward_type = Column(String(50), nullable=False)  # postcard / knowledge_note / blessing
    reward_name = Column(String(200), nullable=False)
    reward_content = Column(String(500), nullable=True)
    reward_image = Column(String(500), nullable=True)
    rarity = Column(String(20), default="common")  # common / rare / epic
    source_location = Column(String(100), nullable=True)
    is_new = Column(Integer, default=1)  # 1 = new, 0 = seen
    created_at = Column(DateTime, server_default=func.now())
