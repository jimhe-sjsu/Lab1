from __future__ import annotations

from backend_shared.query_helpers import score_restaurant_for_ai, search_restaurant_documents, serialize_restaurant_list


def build_ai_response(db, current_user: dict, message: str, conversation_history: list[dict]):
    preferences = db.preferences.find_one({"user_id": current_user["id"]}) or {}
    restaurants = serialize_restaurant_list(db, search_restaurant_documents(db, {}))

    scored = []
    for restaurant in restaurants:
        score, reason = score_restaurant_for_ai(restaurant, message, preferences)
        scored.append((score, reason, restaurant))

    scored.sort(key=lambda item: (item[0], item[2].get("review_count", 0)), reverse=True)
    recommendations = [
        {
            "id": item["id"],
            "name": item["name"],
            "cuisine": item["cuisine_type"],
            "average_rating": item["average_rating"],
            "review_count": item["review_count"],
            "price_tier": item.get("price_tier") or "$$",
            "reason": reason,
        }
        for _, reason, item in scored[:5]
    ]

    reply = "I found a few good matches based on your request."
    if not recommendations:
        reply = "I could not find a strong match yet. Try adding a cuisine, city, or dining vibe."

    return {
        "reply": reply,
        "applied_filters": {
            "message": message,
            "conversation_length": len(conversation_history),
            "preferred_cuisines": preferences.get("preferred_cuisines", []),
            "preferred_locations": preferences.get("preferred_locations", []),
        },
        "recommendations": recommendations,
    }
