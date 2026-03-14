from sqlalchemy import Column, Integer, ForeignKey, DateTime
from app.database import Base
from datetime import datetime


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)