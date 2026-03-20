from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.models.user import User, UserPreference, UserRole
from app.schemas.user import (
    RestaurantHistoryItem,
    ReviewHistoryItem,
    UserHistoryResponse,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserProfileResponse,
    UserProfileUpdate,
)

router = APIRouter(prefix="/users", tags=["Users"])


PROFILE_FIELDS = [
    "name",
    "email",
    "phone_number",
    "about_me",
    "city",
    "state",
    "country",
    "languages",
    "gender",
    "profile_image_url",
]


def _to_csv(values: List[str]) -> str:
    cleaned = [value.strip() for value in values if value and value.strip()]
    return ",".join(cleaned)


def _from_csv(value: str) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _serialize_profile(user: User) -> UserProfileResponse:
    return UserProfileResponse(
        id=user.id,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        name=user.name,
        email=user.email,
        phone_number=user.phone_number,
        about_me=user.about_me,
        city=user.city,
        state=user.state,
        country=user.country,
        languages=user.languages,
        gender=user.gender,
        profile_image_url=user.profile_image_url,
    )


def _get_or_create_preferences(db: Session, user_id: int) -> UserPreference:
    preferences = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if preferences:
        return preferences

    preferences = UserPreference(user_id=user_id)
    db.add(preferences)
    db.commit()
    db.refresh(preferences)
    return preferences


def _serialize_preferences(preferences: UserPreference) -> UserPreferencesResponse:
    return UserPreferencesResponse(
        user_id=preferences.user_id,
        preferred_cuisines=_from_csv(preferences.preferred_cuisines),
        price_range=preferences.price_range,
        preferred_locations=_from_csv(preferences.preferred_locations),
        dietary_needs=_from_csv(preferences.dietary_needs),
        ambiance_preferences=_from_csv(preferences.ambiance_preferences),
        sort_preference=preferences.sort_preference,
    )


@router.get("/me", response_model=UserProfileResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return _serialize_profile(current_user)


@router.put("/me", response_model=UserProfileResponse)
def update_me(
    updates: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    update_data = updates.model_dump(exclude_unset=True)

    new_email = update_data.get("email")
    if new_email and new_email != current_user.email:
        existing = db.query(User).filter(User.email == new_email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

    if "role" in update_data and update_data["role"]:
        try:
            current_user.role = UserRole(update_data["role"])
        except ValueError as error:
            raise HTTPException(status_code=400, detail="Invalid role value") from error

    for field in PROFILE_FIELDS:
        if field in update_data:
            setattr(current_user, field, update_data[field])

    db.commit()
    db.refresh(current_user)
    return _serialize_profile(current_user)


@router.get("/me/preferences", response_model=UserPreferencesResponse)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    preferences = _get_or_create_preferences(db, current_user.id)
    return _serialize_preferences(preferences)


@router.put("/me/preferences", response_model=UserPreferencesResponse)
def update_preferences(
    updates: UserPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    preferences = _get_or_create_preferences(db, current_user.id)

    preferences.preferred_cuisines = _to_csv(updates.preferred_cuisines)
    preferences.price_range = updates.price_range
    preferences.preferred_locations = _to_csv(updates.preferred_locations)
    preferences.dietary_needs = _to_csv(updates.dietary_needs)
    preferences.ambiance_preferences = _to_csv(updates.ambiance_preferences)
    preferences.sort_preference = updates.sort_preference

    db.commit()
    db.refresh(preferences)

    return _serialize_preferences(preferences)


@router.get("/me/history", response_model=UserHistoryResponse)
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reviews = (
        db.query(Review, Restaurant.name)
        .join(Restaurant, Restaurant.id == Review.restaurant_id)
        .filter(Review.user_id == current_user.id)
        .order_by(Review.created_at.desc())
        .all()
    )

    restaurants = (
        db.query(Restaurant)
        .filter(Restaurant.created_by == current_user.id)
        .order_by(Restaurant.created_at.desc())
        .all()
    )

    review_items = [
        ReviewHistoryItem(
            review_id=review.id,
            restaurant_id=review.restaurant_id,
            restaurant_name=restaurant_name,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
        )
        for review, restaurant_name in reviews
    ]

    restaurant_items = [
        RestaurantHistoryItem(
            restaurant_id=restaurant.id,
            name=restaurant.name,
            cuisine_type=restaurant.cuisine_type,
            city=restaurant.city,
            created_at=restaurant.created_at,
        )
        for restaurant in restaurants
    ]

    return UserHistoryResponse(
        reviews_written=review_items,
        restaurants_added=restaurant_items,
    )
