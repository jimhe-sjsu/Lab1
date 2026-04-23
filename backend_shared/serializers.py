from __future__ import annotations

from typing import Any


def clean_document(document: dict[str, Any] | None) -> dict[str, Any] | None:
    if document is None:
        return None
    return {key: value for key, value in document.items() if key != "_id"}


def serialize_user_profile(user: dict[str, Any]) -> dict[str, Any]:
    payload = clean_document(user) or {}
    return {
        "id": payload["id"],
        "role": payload.get("role", "USER"),
        "name": payload.get("name"),
        "email": payload.get("email"),
        "phone_number": payload.get("phone_number"),
        "about_me": payload.get("about_me"),
        "city": payload.get("city"),
        "state": payload.get("state"),
        "country": payload.get("country"),
        "languages": payload.get("languages"),
        "gender": payload.get("gender"),
        "profile_image_url": payload.get("profile_image_url"),
        "restaurant_location": payload.get("restaurant_location"),
    }


def serialize_preferences(preferences: dict[str, Any] | None, user_id: int) -> dict[str, Any]:
    payload = clean_document(preferences) or {}
    return {
        "user_id": user_id,
        "preferred_cuisines": payload.get("preferred_cuisines", []),
        "price_range": payload.get("price_range"),
        "preferred_locations": payload.get("preferred_locations", []),
        "search_radius": payload.get("search_radius"),
        "dietary_needs": payload.get("dietary_needs", []),
        "ambiance_preferences": payload.get("ambiance_preferences", []),
        "sort_preference": payload.get("sort_preference"),
    }


def serialize_review(review: dict[str, Any], reviewer_name: str | None = None) -> dict[str, Any]:
    payload = clean_document(review) or {}
    payload["reviewer_name"] = reviewer_name
    return payload


def serialize_restaurant(restaurant: dict[str, Any], average_rating: float = 0, review_count: int = 0) -> dict[str, Any]:
    payload = clean_document(restaurant) or {}
    payload["average_rating"] = float(average_rating or 0)
    payload["review_count"] = int(review_count or 0)
    payload["view_count"] = int(payload.get("view_count") or 0)
    return payload


def serialize_review_job(review_job: dict[str, Any]) -> dict[str, Any]:
    payload = clean_document(review_job) or {}
    return {
        "job_id": payload["job_id"],
        "status": payload.get("status", "queued"),
        "operation": payload.get("operation", "unknown"),
        "review_id": payload.get("review_id"),
        "restaurant_id": payload.get("restaurant_id"),
        "error": payload.get("error"),
    }
