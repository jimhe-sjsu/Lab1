from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from backend_shared.activity import record_activity
from backend_shared.auth import get_current_user, get_token_payload, hash_password, issue_session, revoke_session, verify_password
from backend_shared.db import get_database
from backend_shared.ids import get_next_id
from backend_shared.query_helpers import build_owner_dashboard
from backend_shared.schemas import MessageResponse, OwnerDashboardResponse, SignupRequest, TokenResponse, UserProfileResponse, UserProfileUpdate
from backend_shared.serializers import serialize_user_profile
from backend_shared.service_factory import create_service_app
from backend_shared.utils import normalize_text, utcnow

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
    "restaurant_location",
]

app = create_service_app(
    title="Lab 2 Owner Service",
    description="Restaurant owner identity, profile, claim flow, and owner analytics.",
)


def _owner_location_matches_restaurant(owner_location: str | None, restaurant: dict) -> bool:
    owner_location_normalized = normalize_text(owner_location)
    if not owner_location_normalized:
        return False

    restaurant_parts = [
        restaurant.get("address"),
        restaurant.get("city"),
        restaurant.get("state"),
        restaurant.get("zip_code"),
        f"{restaurant.get('city', '')} {restaurant.get('state', '')}",
        f"{restaurant.get('address', '')} {restaurant.get('city', '')} {restaurant.get('state', '')} {restaurant.get('zip_code', '')}",
    ]

    normalized_parts = [normalize_text(part) for part in restaurant_parts if part]
    return any(
        part and (part in owner_location_normalized or owner_location_normalized in part)
        for part in normalized_parts
    )


@app.post("/auth/signup", response_model=MessageResponse)
def signup(payload: SignupRequest):
    db = get_database()
    if db.users.find_one({"email": payload.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = get_next_id(db, "users")
    db.users.insert_one(
        {
            "id": user_id,
            "name": payload.name,
            "email": payload.email,
            "password_hash": hash_password(payload.password),
            "role": "OWNER",
            "phone_number": None,
            "about_me": None,
            "city": None,
            "state": None,
            "country": None,
            "languages": None,
            "gender": None,
            "profile_image_url": None,
            "restaurant_location": payload.restaurant_location,
            "created_at": utcnow(),
        }
    )
    return MessageResponse(message="Owner account created successfully")


@app.post("/auth/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_database()
    user = db.users.find_one({"email": form_data.username})

    if not user or user.get("role") != "OWNER" or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    return TokenResponse(**issue_session(db, user=user, service_name="owner-service"))


@app.post("/auth/logout", response_model=MessageResponse)
def logout(payload: dict = Depends(get_token_payload), current_user: dict = Depends(get_current_user({"OWNER"}))):
    revoke_session(payload["sid"])
    return MessageResponse(message="Logged out successfully")


@app.get("/users/me", response_model=UserProfileResponse)
def get_me(current_user: dict = Depends(get_current_user({"OWNER"}))):
    return UserProfileResponse(**serialize_user_profile(current_user))


@app.put("/users/me", response_model=UserProfileResponse)
def update_me(updates: UserProfileUpdate, current_user: dict = Depends(get_current_user({"OWNER"}))):
    db = get_database()
    update_data = updates.model_dump(exclude_unset=True)

    new_email = update_data.get("email")
    if new_email and new_email != current_user["email"]:
        existing = db.users.find_one({"email": new_email, "id": {"$ne": current_user["id"]}})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

    changes = {}
    for field in PROFILE_FIELDS:
        if field in update_data:
            changes[field] = update_data[field]

    if changes:
        db.users.update_one({"id": current_user["id"]}, {"$set": changes})

    refreshed = db.users.find_one({"id": current_user["id"]})
    return UserProfileResponse(**serialize_user_profile(refreshed))


@app.post("/restaurants/{restaurant_id}/claim")
def claim_restaurant(restaurant_id: int, current_user: dict = Depends(get_current_user({"OWNER"}))):
    db = get_database()
    restaurant = db.restaurants.find_one({"id": restaurant_id})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if restaurant.get("owner_id") == current_user["id"]:
        return {"message": "You already manage this restaurant"}
    if restaurant.get("owner_id") and restaurant.get("owner_id") != current_user["id"]:
        raise HTTPException(status_code=400, detail="This restaurant has already been claimed")
    if not current_user.get("restaurant_location"):
        raise HTTPException(
            status_code=400,
            detail="Please update your owner profile with a restaurant location before claiming a listing",
        )
    if not _owner_location_matches_restaurant(current_user.get("restaurant_location"), restaurant):
        raise HTTPException(
            status_code=400,
            detail="Owner restaurant location does not match this listing. Update your owner profile first.",
        )

    db.restaurants.update_one({"id": restaurant_id}, {"$set": {"owner_id": current_user["id"]}})
    record_activity(
        db,
        user_id=current_user["id"],
        event_type="restaurant.claimed",
        restaurant_id=restaurant_id,
        metadata={"restaurant_name": restaurant.get("name")},
    )
    return {"message": "Restaurant claimed successfully"}


@app.get("/restaurants/{restaurant_id}/dashboard", response_model=OwnerDashboardResponse)
def restaurant_dashboard(restaurant_id: int, current_user: dict = Depends(get_current_user({"OWNER"}))):
    db = get_database()
    dashboard = build_owner_dashboard(db, restaurant_id, current_user["id"])
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if dashboard is False:
        raise HTTPException(status_code=403, detail="Not authorized")
    return dashboard
