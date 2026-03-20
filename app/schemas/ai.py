from typing import List, Literal

from pydantic import BaseModel, Field


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
