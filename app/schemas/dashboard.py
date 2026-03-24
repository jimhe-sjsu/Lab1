from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


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
