from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UserRole(str, Enum):
    USER = "USER"
    OWNER = "OWNER"


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=128)
    role: UserRole = UserRole.USER
    restaurant_location: Optional[str] = None

    @model_validator(mode="after")
    def validate_owner_location(self):
        if self.role == UserRole.OWNER and not (self.restaurant_location or "").strip():
            raise ValueError("Restaurant location is required for owner signup")
        return self


class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    session_id: str
    expires_at: datetime


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
    search_radius: Optional[int] = None
    dietary_needs: List[str] = Field(default_factory=list)
    ambiance_preferences: List[str] = Field(default_factory=list)
    sort_preference: Optional[str] = None


class UserPreferencesUpdate(UserPreferencesBase):
    pass


class UserPreferencesResponse(UserPreferencesBase):
    user_id: int

    model_config = ConfigDict(from_attributes=True)


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


class ReviewJobResponse(BaseModel):
    job_id: str
    status: str
    operation: str
    review_id: Optional[int] = None
    restaurant_id: Optional[int] = None
    error: Optional[str] = None


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


class RecentReviewItem(BaseModel):
    id: int
    reviewer_name: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime


class SentimentSummary(BaseModel):
    positive: int
    neutral: int
    negative: int


class OwnerDashboardResponse(BaseModel):
    restaurant: str
    total_reviews: int
    average_rating: float
    favorite_count: int
    total_views: int
    rating_distribution: Dict[str, int]
    recent_reviews: List[RecentReviewItem]
    sentiment_summary: SentimentSummary


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_history: List[ConversationMessage] = Field(default_factory=list)


class AIRecommendation(BaseModel):
    id: int
    name: str
    cuisine: str
    average_rating: float
    review_count: int
    price_tier: str
    reason: str


class AIChatResponse(BaseModel):
    reply: str
    applied_filters: dict
    recommendations: List[AIRecommendation]


class UploadResponse(BaseModel):
    url: str
    filename: str
