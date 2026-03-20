from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


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

    # Additional optional metadata for richer listing details.
    contact_phone = Column(String(30), nullable=True)
    hours_text = Column(String(255), nullable=True)
    photo_url = Column(String(500), nullable=True)
    amenities_text = Column(String(500), nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    reviews = relationship("Review", back_populates="restaurant", cascade="all, delete")
