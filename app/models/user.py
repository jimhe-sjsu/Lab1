from datetime import datetime
import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    USER = "USER"
    OWNER = "OWNER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)

    # Profile fields required by the assignment.
    phone_number = Column(String(30), nullable=True)
    about_me = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(10), nullable=True)
    country = Column(String(100), nullable=True)
    languages = Column(String(200), nullable=True)
    gender = Column(String(30), nullable=True)
    profile_image_url = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    preferences = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    preferred_cuisines = Column(String(500), nullable=True)
    price_range = Column(String(20), nullable=True)
    preferred_locations = Column(String(500), nullable=True)
    dietary_needs = Column(String(500), nullable=True)
    ambiance_preferences = Column(String(500), nullable=True)
    sort_preference = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preferences")
