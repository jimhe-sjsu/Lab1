from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserProfileBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    languages: Optional[str] = None
    gender: Optional[str] = None
    profile_image_url: Optional[str] = None
    restaurant_location: Optional[str] = None


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileResponse(UserProfileBase):
    id: int
    role: str

    model_config = ConfigDict(from_attributes=True)


class UserPreferencesBase(BaseModel):
    preferred_cuisines: List[str] = Field(default_factory=list)
    price_range: Optional[str] = None
    preferred_locations: List[str] = Field(default_factory=list)
    search_radius: Optional[int] = Field(default=None, ge=1, le=100)
    dietary_needs: List[str] = Field(default_factory=list)
    ambiance_preferences: List[str] = Field(default_factory=list)
    sort_preference: Optional[str] = None


class UserPreferencesUpdate(UserPreferencesBase):
    pass


class UserPreferencesResponse(UserPreferencesBase):
    user_id: int


class ReviewHistoryItem(BaseModel):
    review_id: int
    restaurant_id: int
    restaurant_name: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime


class RestaurantHistoryItem(BaseModel):
    restaurant_id: int
    name: str
    cuisine_type: str
    city: str
    created_at: datetime


class UserHistoryResponse(BaseModel):
    reviews_written: List[ReviewHistoryItem]
    restaurants_added: List[RestaurantHistoryItem]
