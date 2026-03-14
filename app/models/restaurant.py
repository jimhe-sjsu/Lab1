from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)
    cuisine_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(10), nullable=False)
    zip_code = Column(String(20), nullable=False)

    price_tier = Column(String(10), nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # IMPORTANT PART
    reviews = relationship("Review", back_populates="restaurant", cascade="all, delete")