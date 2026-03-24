from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.user import UserRole


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
