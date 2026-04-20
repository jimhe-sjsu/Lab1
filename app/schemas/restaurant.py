from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.review import ReviewResponse


class RestaurantBase(BaseModel):
    name: str
    cuisine_type: str
    address: str
    city: str
    state: str
    zip_code: str
    description: Optional[str] = None
    price_tier: Optional[str] = None
    contact_phone: Optional[str] = None
    hours_text: Optional[str] = None
    photo_url: Optional[str] = None
    amenities_text: Optional[str] = None


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    cuisine_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    description: Optional[str] = None
    price_tier: Optional[str] = None
    contact_phone: Optional[str] = None
    hours_text: Optional[str] = None
    photo_url: Optional[str] = None
    amenities_text: Optional[str] = None


class RestaurantResponse(RestaurantBase):
    id: int
    created_by: int
    owner_id: Optional[int]
    average_rating: float = 0
    review_count: int = 0
    view_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class RestaurantDetailsResponse(BaseModel):
    restaurant: RestaurantResponse
    average_rating: float
    review_count: int
    reviews: List[ReviewResponse]
