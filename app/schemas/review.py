from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    restaurant_id: int
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    photo_url: Optional[str] = None


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = None
    photo_url: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    restaurant_id: int
    rating: int
    comment: Optional[str]
    photo_url: Optional[str]
    user_id: int
    reviewer_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
