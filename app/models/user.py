from sqlalchemy import Column, Integer, String, DateTime, Enum
from app.database import Base
import enum
from datetime import datetime


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
    created_at = Column(DateTime, default=datetime.utcnow)