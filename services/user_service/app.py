from __future__ import annotations

from pathlib import Path

from fastapi import Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles

from backend_shared.ai import build_ai_response
from backend_shared.auth import get_current_user, get_token_payload, hash_password, issue_session, revoke_session, verify_password
from backend_shared.config import get_settings
from backend_shared.db import get_database
from backend_shared.ids import get_next_id
from backend_shared.query_helpers import fetch_reviews_with_authors, search_restaurant_documents, serialize_restaurant_list
from backend_shared.schemas import (
    AIChatRequest,
    AIChatResponse,
    MessageResponse,
    SignupRequest,
    TokenResponse,
    UploadResponse,
    UserHistoryResponse,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserProfileResponse,
    UserProfileUpdate,
)
from backend_shared.serializers import serialize_preferences, serialize_user_profile
from backend_shared.service_factory import create_service_app
from backend_shared.uploads import get_upload_directory, load_upload, save_upload
from backend_shared.utils import utcnow
from backend_shared.activity import record_activity

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
    title="Lab 2 User Service",
    description="Reviewer identity, profile, preferences, favourites, uploads, and AI endpoints.",
)

upload_dir = get_upload_directory()
upload_dir.mkdir(parents=True, exist_ok=True)


def _get_preferences_document(db, user_id: int):
    document = db.preferences.find_one({"user_id": user_id})
    if document:
        return document

    now = utcnow()
    document = {
        "user_id": user_id,
        "preferred_cuisines": [],
        "price_range": None,
        "preferred_locations": [],
        "search_radius": None,
        "dietary_needs": [],
        "ambiance_preferences": [],
        "sort_preference": None,
        "created_at": now,
        "updated_at": now,
    }
    db.preferences.insert_one(document)
    return document


@app.post("/auth/signup", response_model=MessageResponse)
def signup(payload: SignupRequest):
    if payload.role.value != "USER":
        raise HTTPException(status_code=400, detail="Use the owner service to create owner accounts")

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
            "role": "USER",
            "phone_number": None,
            "about_me": None,
            "city": None,
            "state": None,
            "country": None,
            "languages": None,
            "gender": None,
            "profile_image_url": None,
            "restaurant_location": None,
            "created_at": utcnow(),
        }
    )
    return MessageResponse(message="User created successfully")


@app.post("/auth/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_database()
    user = db.users.find_one({"email": form_data.username})

    if not user or user.get("role") != "USER" or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    return TokenResponse(**issue_session(db, user=user, service_name="user-service"))


@app.post("/auth/logout", response_model=MessageResponse)
def logout(payload: dict = Depends(get_token_payload), current_user: dict = Depends(get_current_user())):
    revoke_session(payload["sid"])
    return MessageResponse(message="Logged out successfully")


@app.get("/users/me", response_model=UserProfileResponse)
def get_me(current_user: dict = Depends(get_current_user())):
    return UserProfileResponse(**serialize_user_profile(current_user))


@app.put("/users/me", response_model=UserProfileResponse)
def update_me(updates: UserProfileUpdate, current_user: dict = Depends(get_current_user())):
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


@app.get("/users/me/preferences", response_model=UserPreferencesResponse)
def get_preferences(current_user: dict = Depends(get_current_user())):
    db = get_database()
    preferences = _get_preferences_document(db, current_user["id"])
    return UserPreferencesResponse(**serialize_preferences(preferences, current_user["id"]))


@app.put("/users/me/preferences", response_model=UserPreferencesResponse)
def update_preferences(payload: UserPreferencesUpdate, current_user: dict = Depends(get_current_user())):
    db = get_database()
    document = {
        "preferred_cuisines": payload.preferred_cuisines,
        "price_range": payload.price_range,
        "preferred_locations": payload.preferred_locations,
        "search_radius": payload.search_radius,
        "dietary_needs": payload.dietary_needs,
        "ambiance_preferences": payload.ambiance_preferences,
        "sort_preference": payload.sort_preference,
        "updated_at": utcnow(),
    }
    if not db.preferences.find_one({"user_id": current_user["id"]}):
        document["created_at"] = utcnow()
    db.preferences.update_one({"user_id": current_user["id"]}, {"$set": document}, upsert=True)
    preferences = db.preferences.find_one({"user_id": current_user["id"]})
    return UserPreferencesResponse(**serialize_preferences(preferences, current_user["id"]))


@app.get("/users/me/history", response_model=UserHistoryResponse)
def get_history(current_user: dict = Depends(get_current_user())):
    db = get_database()
    reviews = list(db.reviews.find({"user_id": current_user["id"]}).sort("created_at", -1))
    restaurants = list(db.restaurants.find({"created_by": current_user["id"]}).sort("created_at", -1))
    restaurant_map = {restaurant["id"]: restaurant["name"] for restaurant in db.restaurants.find({}, {"id": 1, "name": 1})}

    return UserHistoryResponse(
        reviews_written=[
            {
                "review_id": review["id"],
                "restaurant_id": review["restaurant_id"],
                "restaurant_name": restaurant_map.get(review["restaurant_id"], "Unknown restaurant"),
                "rating": review["rating"],
                "comment": review.get("comment"),
                "created_at": review["created_at"],
            }
            for review in reviews
        ],
        restaurants_added=[
            {
                "restaurant_id": restaurant["id"],
                "name": restaurant["name"],
                "cuisine_type": restaurant["cuisine_type"],
                "city": restaurant["city"],
                "created_at": restaurant["created_at"],
            }
            for restaurant in restaurants
        ],
    )


@app.get("/dashboard/user")
def user_dashboard(current_user: dict = Depends(get_current_user())):
    db = get_database()
    total_reviews = db.reviews.count_documents({"user_id": current_user["id"]})
    total_favorites = db.favorites.count_documents({"user_id": current_user["id"]})
    return {
        "user": current_user["email"],
        "total_reviews": int(total_reviews),
        "total_favorites": int(total_favorites),
    }


@app.post("/favorites/{restaurant_id}")
def add_favorite(restaurant_id: int, current_user: dict = Depends(get_current_user())):
    db = get_database()
    restaurant = db.restaurants.find_one({"id": restaurant_id})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if db.favorites.find_one({"user_id": current_user["id"], "restaurant_id": restaurant_id}):
        raise HTTPException(status_code=400, detail="Already in favorites")

    favorite_id = get_next_id(db, "favorites")
    db.favorites.insert_one(
        {
            "id": favorite_id,
            "user_id": current_user["id"],
            "restaurant_id": restaurant_id,
            "created_at": utcnow(),
        }
    )
    record_activity(db, user_id=current_user["id"], event_type="favorite.added", favorite_id=favorite_id, restaurant_id=restaurant_id)
    return {"message": "Added to favorites"}


@app.get("/favorites/")
def get_my_favorites(current_user: dict = Depends(get_current_user())):
    db = get_database()
    return list(db.favorites.find({"user_id": current_user["id"]}, {"_id": 0}).sort("created_at", -1))


@app.delete("/favorites/{restaurant_id}")
def remove_favorite(restaurant_id: int, current_user: dict = Depends(get_current_user())):
    db = get_database()
    favorite = db.favorites.find_one({"user_id": current_user["id"], "restaurant_id": restaurant_id})
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.favorites.delete_one({"id": favorite["id"]})
    return {"message": "Removed from favorites"}


@app.post("/ai-assistant/chat", response_model=AIChatResponse)
def ai_chat(payload: AIChatRequest, current_user: dict = Depends(get_current_user())):
    db = get_database()
    response = build_ai_response(
        db,
        current_user=current_user,
        message=payload.message,
        conversation_history=[item.model_dump() for item in payload.conversation_history],
    )
    return AIChatResponse(**response)


@app.post("/uploads/image", response_model=UploadResponse)
def upload_image(file: UploadFile = File(...), current_user: dict = Depends(get_current_user())):
    upload = save_upload(file)
    return UploadResponse(**upload)


@app.get("/uploads/{filename}")
def get_uploaded_image(filename: str):
    upload = load_upload(filename)
    return Response(content=upload["body"], media_type=upload["content_type"])


app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")
