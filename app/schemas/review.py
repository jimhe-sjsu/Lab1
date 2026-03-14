from pydantic import BaseModel
from typing import Optional


class ReviewCreate(BaseModel):
    restaurant_id: int
    rating: int
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    restaurant_id: int
    rating: int
    comment: Optional[str]
    user_id: int

    class Config:
        from_attributes = True