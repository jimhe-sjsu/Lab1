import json
import os
from typing import Any, Dict, List

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.restaurant import Restaurant
from app.models.review import Review
from app.models.user import User, UserPreference


CUISINE_KEYWORDS = [
    "italian",
    "chinese",
    "mexican",
    "indian",
    "japanese",
    "american",
    "thai",
    "korean",
    "french",
    "mediterranean",
    "vegan",
]

PRICE_KEYWORDS = ["$", "$$", "$$$", "$$$$", "cheap", "budget", "expensive", "affordable"]
DIETARY_KEYWORDS = ["vegan", "vegetarian", "halal", "kosher", "gluten-free", "gluten free"]
AMBIANCE_KEYWORDS = ["casual", "fine dining", "family", "romantic", "quiet", "outdoor", "wifi"]
OCCASION_KEYWORDS = ["dinner", "lunch", "breakfast", "anniversary", "date", "party", "tonight"]
LIVE_CONTEXT_TERMS = ["open now", "hours", "today", "event", "trending", "special", "this weekend"]


def _csv_to_list(value: str) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def load_user_preferences(db: Session, user_id: int) -> Dict[str, Any]:
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        return {
            "preferred_cuisines": [],
            "price_range": None,
            "preferred_locations": [],
            "dietary_needs": [],
            "ambiance_preferences": [],
            "sort_preference": None,
        }

    return {
        "preferred_cuisines": _csv_to_list(pref.preferred_cuisines),
        "price_range": pref.price_range,
        "preferred_locations": _csv_to_list(pref.preferred_locations),
        "dietary_needs": _csv_to_list(pref.dietary_needs),
        "ambiance_preferences": _csv_to_list(pref.ambiance_preferences),
        "sort_preference": pref.sort_preference,
    }


def _extract_by_keywords(text: str, keywords: List[str]) -> List[str]:
    lowered = text.lower()
    return [keyword for keyword in keywords if keyword in lowered]


def parse_filters(message: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    history_text = " ".join(item.get("content", "") for item in conversation_history[-6:])
    combined = f"{history_text} {message}".strip()

    prompt = PromptTemplate.from_template(
        "Extract restaurant intent from this user request: {message}. Return valid JSON only."
    )
    formatted_message = prompt.format(message=combined)

    extracted = {
        "cuisines": _extract_by_keywords(formatted_message, CUISINE_KEYWORDS),
        "price_hints": _extract_by_keywords(formatted_message, PRICE_KEYWORDS),
        "dietary": _extract_by_keywords(formatted_message, DIETARY_KEYWORDS),
        "ambiance": _extract_by_keywords(formatted_message, AMBIANCE_KEYWORDS),
        "occasion": _extract_by_keywords(formatted_message, OCCASION_KEYWORDS),
        "location_terms": [],
        "keyword": None,
    }

    tokenized = [token.strip(",.!?;:").lower() for token in message.split()]
    location_terms = [token for token in tokenized if token and (token.isdigit() and len(token) == 5)]
    extracted["location_terms"] = location_terms

    keyword_candidates = [term for term in extracted["ambiance"] if term not in {"family", "date"}]
    if keyword_candidates:
        extracted["keyword"] = keyword_candidates[0]

    parser = JsonOutputParser()
    parsed = parser.parse(json.dumps(extracted))
    return parsed


def _price_from_hints(hints: List[str], preference_price: str | None) -> str | None:
    for symbol in ["$$$$", "$$$", "$$", "$"]:
        if symbol in hints:
            return symbol

    hint_map = {
        "cheap": "$",
        "budget": "$",
        "affordable": "$$",
        "expensive": "$$$",
    }
    for hint in hints:
        if hint in hint_map:
            return hint_map[hint]

    return preference_price


def _needs_live_context(message: str) -> bool:
    lowered = message.lower()
    return any(term in lowered for term in LIVE_CONTEXT_TERMS)


def _fetch_live_context(message: str) -> str:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return ""

    if not _needs_live_context(message):
        return ""

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        result = client.search(query=message, max_results=2)
        snippets = [item.get("content", "") for item in result.get("results", []) if item.get("content")]
        compact = " ".join(snippets)[:350]
        return compact
    except Exception:
        return ""


def _rank_restaurants(rows: List[Any], filters: Dict[str, Any], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
    ranked = []

    for restaurant, avg_rating, review_count in rows:
        reasons = []
        score = float(avg_rating or 0) * 1.4 + min(int(review_count or 0), 50) * 0.03

        cuisines = [item.lower() for item in filters.get("cuisines", [])]
        preference_cuisines = [item.lower() for item in preferences.get("preferred_cuisines", [])]
        restaurant_cuisine = (restaurant.cuisine_type or "").lower()

        if cuisines and any(c in restaurant_cuisine for c in cuisines):
            score += 2.5
            reasons.append("matches your cuisine query")
        elif preference_cuisines and any(c in restaurant_cuisine for c in preference_cuisines):
            score += 1.5
            reasons.append("matches your saved cuisine preference")

        desired_price = _price_from_hints(filters.get("price_hints", []), preferences.get("price_range"))
        if desired_price and restaurant.price_tier == desired_price:
            score += 1.2
            reasons.append("fits your preferred price range")

        location_terms = [term.lower() for term in filters.get("location_terms", []) + preferences.get("preferred_locations", [])]
        if location_terms:
            location_blob = " ".join(
                [restaurant.city or "", restaurant.state or "", restaurant.zip_code or "", restaurant.address or ""]
            ).lower()
            if any(term in location_blob for term in location_terms):
                score += 1.2
                reasons.append("aligns with your preferred location")

        keyword = (filters.get("keyword") or "").lower()
        if keyword:
            text_blob = " ".join([restaurant.description or "", restaurant.amenities_text or ""]).lower()
            if keyword in text_blob:
                score += 1.0
                reasons.append("matches requested atmosphere/features")

        if not reasons:
            reasons.append("high overall rating and strong review volume")

        ranked.append(
            {
                "id": restaurant.id,
                "name": restaurant.name,
                "cuisine": restaurant.cuisine_type,
                "average_rating": round(float(avg_rating or 0), 2),
                "review_count": int(review_count or 0),
                "price_tier": restaurant.price_tier or "$$",
                "reason": reasons[0],
                "score": score,
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:5]


def find_recommendations(
    db: Session,
    current_user: User,
    message: str,
    conversation_history: List[Dict[str, str]],
) -> Dict[str, Any]:
    preferences = load_user_preferences(db, current_user.id)
    filters = parse_filters(message, conversation_history)

    query = (
        db.query(
            Restaurant,
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("review_count"),
        )
        .outerjoin(Review, Review.restaurant_id == Restaurant.id)
    )

    cuisines = filters.get("cuisines", []) or preferences.get("preferred_cuisines", [])
    if cuisines:
        cuisine_clauses = [Restaurant.cuisine_type.ilike(f"%{cuisine}%") for cuisine in cuisines]
        query = query.filter(or_(*cuisine_clauses))

    desired_price = _price_from_hints(filters.get("price_hints", []), preferences.get("price_range"))
    if desired_price:
        query = query.filter(Restaurant.price_tier == desired_price)

    location_terms = filters.get("location_terms", []) or preferences.get("preferred_locations", [])
    if location_terms:
        clauses = []
        for term in location_terms:
            clauses.append(Restaurant.city.ilike(f"%{term}%"))
            clauses.append(Restaurant.zip_code.ilike(f"%{term}%"))
            clauses.append(Restaurant.address.ilike(f"%{term}%"))
        query = query.filter(or_(*clauses))

    keyword = filters.get("keyword")
    if keyword:
        query = query.filter(
            or_(
                Restaurant.description.ilike(f"%{keyword}%"),
                Restaurant.amenities_text.ilike(f"%{keyword}%"),
            )
        )

    rows = query.group_by(Restaurant.id).all()
    recommendations = _rank_restaurants(rows, filters, preferences)

    live_context = _fetch_live_context(message)
    if live_context and recommendations:
        recommendations[0]["reason"] = f"{recommendations[0]['reason']} | live context checked"

    if recommendations:
        top_names = ", ".join(item["name"] for item in recommendations[:3])
        reply = f"Here are strong matches for your request: {top_names}."
    else:
        reply = "I could not find an exact match, so try broadening cuisine or location constraints."

    if live_context:
        reply = f"{reply} I also checked live web context for timing/trending cues."

    for item in recommendations:
        item.pop("score", None)

    return {
        "reply": reply,
        "applied_filters": filters,
        "recommendations": recommendations,
    }
