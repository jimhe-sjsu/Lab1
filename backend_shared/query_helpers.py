from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from backend_shared.schemas import OwnerDashboardResponse, RecentReviewItem, SentimentSummary
from backend_shared.serializers import serialize_restaurant, serialize_review
from backend_shared.utils import normalize_text


def _regex_filter(value: str):
    return {"$regex": re.escape(value.strip()), "$options": "i"}


def build_review_metrics(db, restaurant_ids: list[int]) -> dict[int, dict[str, Any]]:
    if not restaurant_ids:
        return {}

    pipeline = [
        {"$match": {"restaurant_id": {"$in": restaurant_ids}}},
        {
            "$group": {
                "_id": "$restaurant_id",
                "average_rating": {"$avg": "$rating"},
                "review_count": {"$sum": 1},
            }
        },
    ]

    metrics = {}
    for document in db.reviews.aggregate(pipeline):
        metrics[int(document["_id"])] = {
            "average_rating": float(document.get("average_rating") or 0),
            "review_count": int(document.get("review_count") or 0),
        }
    return metrics


def fetch_reviews_with_authors(db, restaurant_id: int) -> list[dict[str, Any]]:
    reviews = list(db.reviews.find({"restaurant_id": restaurant_id}).sort("created_at", -1))
    if not reviews:
        return []

    user_ids = sorted({int(review["user_id"]) for review in reviews})
    users = {
        user["id"]: user
        for user in db.users.find({"id": {"$in": user_ids}}, {"id": 1, "name": 1})
    }
    return [
        serialize_review(review, (users.get(review["user_id"]) or {}).get("name"))
        for review in reviews
    ]


def search_restaurant_documents(db, filters: dict[str, Any]) -> list[dict[str, Any]]:
    query: dict[str, Any] = {}

    if filters.get("name"):
        query["name"] = _regex_filter(filters["name"])
    if filters.get("cuisine"):
        query["cuisine_type"] = _regex_filter(filters["cuisine"])
    if filters.get("city"):
        query["city"] = _regex_filter(filters["city"])
    if filters.get("zip_code"):
        query["zip_code"] = _regex_filter(filters["zip_code"])
    if filters.get("price_tier"):
        query["price_tier"] = filters["price_tier"]

    if filters.get("keyword"):
        pattern = _regex_filter(filters["keyword"])
        query["$or"] = [
            {"description": pattern},
            {"amenities_text": pattern},
            {"hours_text": pattern},
            {"name": pattern},
            {"city": pattern},
            {"address": pattern},
        ]

    return list(db.restaurants.find(query).sort("created_at", -1))


def serialize_restaurant_list(db, restaurants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    restaurant_ids = [int(restaurant["id"]) for restaurant in restaurants]
    metrics = build_review_metrics(db, restaurant_ids)
    return [
        serialize_restaurant(
            restaurant,
            average_rating=metrics.get(int(restaurant["id"]), {}).get("average_rating", 0),
            review_count=metrics.get(int(restaurant["id"]), {}).get("review_count", 0),
        )
        for restaurant in restaurants
    ]


def build_restaurant_details(db, restaurant_id: int) -> dict[str, Any] | None:
    restaurant = db.restaurants.find_one({"id": restaurant_id})
    if not restaurant:
        return None

    metrics = build_review_metrics(db, [restaurant_id]).get(restaurant_id, {})
    average_rating = float(metrics.get("average_rating") or 0)
    review_count = int(metrics.get("review_count") or 0)

    return {
        "restaurant": serialize_restaurant(restaurant, average_rating=average_rating, review_count=review_count),
        "average_rating": average_rating,
        "review_count": review_count,
        "reviews": fetch_reviews_with_authors(db, restaurant_id),
    }


def build_owner_dashboard(db, restaurant_id: int, current_owner_id: int) -> OwnerDashboardResponse | None:
    restaurant = db.restaurants.find_one({"id": restaurant_id})
    if not restaurant:
        return None
    if int(restaurant.get("owner_id") or 0) != int(current_owner_id):
        return False

    reviews = list(db.reviews.find({"restaurant_id": restaurant_id}).sort("created_at", -1))
    favorites_count = db.favorites.count_documents({"restaurant_id": restaurant_id})

    rating_distribution = {str(star): 0 for star in range(1, 6)}
    average_rating = 0.0
    if reviews:
        average_rating = sum(int(review["rating"]) for review in reviews) / len(reviews)
        for review in reviews:
            rating_distribution[str(int(review["rating"]))] += 1

    users = {
        user["id"]: user.get("name")
        for user in db.users.find({"id": {"$in": list({review["user_id"] for review in reviews})}}, {"id": 1, "name": 1})
    }

    recent_reviews = [
        RecentReviewItem(
            id=int(review["id"]),
            reviewer_name=users.get(review["user_id"], f"User #{review['user_id']}"),
            rating=int(review["rating"]),
            comment=review.get("comment"),
            created_at=review["created_at"],
        )
        for review in reviews[:5]
    ]

    sentiment = SentimentSummary(
        positive=sum(1 for review in reviews if int(review["rating"]) >= 4),
        neutral=sum(1 for review in reviews if int(review["rating"]) == 3),
        negative=sum(1 for review in reviews if int(review["rating"]) <= 2),
    )

    return OwnerDashboardResponse(
        restaurant=restaurant["name"],
        total_reviews=len(reviews),
        average_rating=average_rating,
        favorite_count=int(favorites_count),
        total_views=int(restaurant.get("view_count") or 0),
        rating_distribution=rating_distribution,
        recent_reviews=recent_reviews,
        sentiment_summary=sentiment,
    )


def score_restaurant_for_ai(restaurant: dict[str, Any], message: str, preferences: dict[str, Any] | None) -> tuple[float, str]:
    haystacks = [
        normalize_text(restaurant.get("name")),
        normalize_text(restaurant.get("cuisine_type")),
        normalize_text(restaurant.get("city")),
        normalize_text(restaurant.get("description")),
        normalize_text(restaurant.get("amenities_text")),
    ]
    message_text = normalize_text(message)
    score = float(restaurant.get("average_rating") or 0)
    reason_bits = []

    if any(token and token in " ".join(haystacks) for token in message_text.split()):
        score += 2.5
        reason_bits.append("Matches your request")

    if preferences:
        preferred_cuisines = [normalize_text(value) for value in preferences.get("preferred_cuisines", [])]
        preferred_locations = [normalize_text(value) for value in preferences.get("preferred_locations", [])]
        if normalize_text(restaurant.get("cuisine_type")) in preferred_cuisines:
            score += 1.5
            reason_bits.append("Matches your preferred cuisine")
        if normalize_text(restaurant.get("city")) in preferred_locations:
            score += 1.0
            reason_bits.append("Matches your preferred location")

    review_count = int(restaurant.get("review_count") or 0)
    score += min(review_count / 25, 2)
    if review_count:
        reason_bits.append(f"Backed by {review_count} review(s)")

    if not reason_bits:
        reason_bits.append("Strong overall rating")

    return score, "; ".join(dict.fromkeys(reason_bits))
