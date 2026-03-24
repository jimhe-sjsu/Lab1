import json
import os
import re
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
    "vegetarian",
]

PRICE_KEYWORDS = ["$", "$$", "$$$", "$$$$", "cheap", "budget", "expensive", "affordable"]
DIETARY_KEYWORDS = ["vegan", "vegetarian", "halal", "kosher", "gluten-free", "gluten free"]
AMBIANCE_KEYWORDS = [
    "casual",
    "fine dining",
    "family-friendly",
    "family",
    "romantic",
    "quiet",
    "outdoor",
    "wifi",
    "cozy",
]
OCCASION_KEYWORDS = ["dinner", "lunch", "breakfast", "anniversary", "date", "party", "tonight", "brunch"]
LIVE_CONTEXT_TERMS = ["open now", "hours", "today", "event", "trending", "special", "this weekend"]



def _csv_to_list(value: str | None) -> List[str]:
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
            "search_radius": None,
            "dietary_needs": [],
            "ambiance_preferences": [],
            "sort_preference": None,
        }

    return {
        "preferred_cuisines": _csv_to_list(pref.preferred_cuisines),
        "price_range": pref.price_range,
        "preferred_locations": _csv_to_list(pref.preferred_locations),
        "search_radius": pref.search_radius,
        "dietary_needs": _csv_to_list(pref.dietary_needs),
        "ambiance_preferences": _csv_to_list(pref.ambiance_preferences),
        "sort_preference": pref.sort_preference,
    }



def _extract_by_keywords(text: str, keywords: List[str]) -> List[str]:
    lowered = text.lower()
    return [keyword for keyword in keywords if keyword in lowered]



def _extract_location_terms(text: str) -> List[str]:
    lowered = text.lower()
    terms = set(re.findall(r"\b\d{5}\b", lowered))

    for match in re.finditer(r"\b(?:in|near|around|at)\s+([a-z][a-z\s,]{1,40})", lowered):
        phrase = match.group(1)
        phrase = re.split(r"\b(?:for|with|that|which|and|or|tonight|today|tomorrow)\b", phrase)[0].strip(" ,.")
        phrase = " ".join(phrase.split())
        if phrase:
            terms.add(phrase)

    return [term for term in terms if term]



def _infer_sort_preference(text: str) -> str | None:
    lowered = text.lower()
    if any(term in lowered for term in ["best rated", "top rated", "highest rated"]):
        return "rating"
    if any(term in lowered for term in ["popular", "trending", "most reviewed"]):
        return "popularity"
    if any(term in lowered for term in ["cheap", "lowest price", "budget"]):
        return "price"
    if any(term in lowered for term in ["near me", "closest", "nearby"]):
        return "distance"
    return None



def parse_filters(message: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    history_text = " ".join(item.get("content", "") for item in conversation_history[-6:])
    combined = f"{history_text} {message}".strip()

    # Keep a LangChain step in the pipeline so the implementation still uses LangChain.
    prompt = PromptTemplate.from_template(
        "Extract restaurant intent from this user request and return JSON only: {message}"
    )
    formatted_message = prompt.format(message=combined)

    extracted = {
        "cuisines": _extract_by_keywords(formatted_message, CUISINE_KEYWORDS),
        "price_hints": _extract_by_keywords(formatted_message, PRICE_KEYWORDS),
        "dietary": _extract_by_keywords(formatted_message, DIETARY_KEYWORDS),
        "ambiance": _extract_by_keywords(formatted_message, AMBIANCE_KEYWORDS),
        "occasion": _extract_by_keywords(formatted_message, OCCASION_KEYWORDS),
        "location_terms": _extract_location_terms(combined),
        "keyword": None,
        "sort_preference": _infer_sort_preference(combined),
    }

    keyword_candidates = [
        term for term in extracted["ambiance"] if term not in {"family", "date", "family-friendly"}
    ]
    if keyword_candidates:
        extracted["keyword"] = keyword_candidates[0]

    parser = JsonOutputParser()
    return parser.parse(json.dumps(extracted))



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
    if not api_key or not _needs_live_context(message):
        return ""

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        result = client.search(query=message, max_results=2)
        snippets = [item.get("content", "") for item in result.get("results", []) if item.get("content")]
        return " ".join(snippets)[:350]
    except Exception:
        return ""



def _price_sort_value(price_tier: str | None) -> int:
    mapping = {"$": 1, "$$": 2, "$$$": 3, "$$$$": 4}
    return mapping.get(price_tier or "$$", 2)



def _rank_restaurants(rows: List[Any], filters: Dict[str, Any], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
    ranked = []

    explicit_cuisines = [item.lower() for item in filters.get("cuisines", [])]
    preference_cuisines = [item.lower() for item in preferences.get("preferred_cuisines", [])]
    desired_price = _price_from_hints(filters.get("price_hints", []), preferences.get("price_range"))
    location_terms = [
        term.lower()
        for term in (filters.get("location_terms", []) + preferences.get("preferred_locations", []))
    ]
    dietary_terms = [item.lower() for item in (filters.get("dietary", []) + preferences.get("dietary_needs", []))]
    ambiance_terms = [item.lower() for item in (filters.get("ambiance", []) + preferences.get("ambiance_preferences", []))]
    occasion_terms = [item.lower() for item in filters.get("occasion", [])]

    for restaurant, avg_rating, review_count in rows:
        reasons = []
        score = float(avg_rating or 0) * 1.5 + min(int(review_count or 0), 75) * 0.04
        restaurant_cuisine = (restaurant.cuisine_type or "").lower()
        text_blob = " ".join(
            [
                restaurant.name or "",
                restaurant.description or "",
                restaurant.amenities_text or "",
                restaurant.hours_text or "",
                restaurant.address or "",
                restaurant.city or "",
                restaurant.state or "",
                restaurant.zip_code or "",
            ]
        ).lower()

        matched_location = False

        if explicit_cuisines and any(cuisine in restaurant_cuisine for cuisine in explicit_cuisines):
            score += 2.6
            reasons.append("matches your cuisine query")
        elif preference_cuisines and any(cuisine in restaurant_cuisine for cuisine in preference_cuisines):
            score += 1.6
            reasons.append("matches your saved cuisine preference")

        if desired_price and restaurant.price_tier == desired_price:
            score += 1.1
            reasons.append("fits your price range")

        if location_terms:
            matched_location = any(term in text_blob for term in location_terms)
            if matched_location:
                score += 1.3
                reasons.append("aligns with your preferred area")

        if dietary_terms and any(term in text_blob or term in restaurant_cuisine for term in dietary_terms):
            score += 1.4
            reasons.append("supports your dietary needs")

        if ambiance_terms and any(term in text_blob for term in ambiance_terms):
            score += 1.2
            reasons.append("matches the atmosphere you asked for")

        if occasion_terms:
            if any(term in occasion_terms for term in ["anniversary", "date"]) and any(
                term in text_blob for term in ["romantic", "fine dining", "outdoor", "cozy"]
            ):
                score += 1.2
                reasons.append("fits a special-occasion dinner")
            elif any(term in occasion_terms for term in ["breakfast", "brunch", "lunch", "dinner"]):
                if restaurant.hours_text:
                    score += 0.6
                    reasons.append("looks like a good timing match")

        keyword = (filters.get("keyword") or "").lower()
        if keyword and keyword in text_blob:
            score += 1.0
            reasons.append("matches requested features")

        ranked.append(
            {
                "id": restaurant.id,
                "name": restaurant.name,
                "cuisine": restaurant.cuisine_type,
                "average_rating": round(float(avg_rating or 0), 2),
                "review_count": int(review_count or 0),
                "price_tier": restaurant.price_tier or "$$",
                "reason": reasons[0] if reasons else "high overall rating and solid review volume",
                "score": score,
                "matched_location": matched_location,
                "price_sort": _price_sort_value(restaurant.price_tier),
            }
        )

    sort_preference = filters.get("sort_preference") or preferences.get("sort_preference") or "rating"

    if sort_preference == "popularity":
        ranked.sort(key=lambda item: (item["review_count"], item["score"]), reverse=True)
    elif sort_preference == "price":
        ranked.sort(key=lambda item: (item["price_sort"], -item["average_rating"]))
    elif sort_preference == "distance":
        ranked.sort(key=lambda item: (item["matched_location"], item["score"]), reverse=True)
    else:
        ranked.sort(key=lambda item: (item["average_rating"], item["score"]), reverse=True)

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
            clauses.append(Restaurant.state.ilike(f"%{term}%"))
        query = query.filter(or_(*clauses))

    keyword = filters.get("keyword")
    if keyword:
        query = query.filter(
            or_(
                Restaurant.description.ilike(f"%{keyword}%"),
                Restaurant.amenities_text.ilike(f"%{keyword}%"),
                Restaurant.hours_text.ilike(f"%{keyword}%"),
            )
        )

    rows = query.group_by(Restaurant.id).all()

    if not rows:
        fallback_rows = (
            db.query(
                Restaurant,
                func.avg(Review.rating).label("avg_rating"),
                func.count(Review.id).label("review_count"),
            )
            .outerjoin(Review, Review.restaurant_id == Restaurant.id)
            .group_by(Restaurant.id)
            .all()
        )
        rows = fallback_rows

    recommendations = _rank_restaurants(rows, filters, preferences)

    live_context = _fetch_live_context(message)
    if live_context and recommendations:
        recommendations[0]["reason"] = f"{recommendations[0]['reason']} and I checked live context"

    if recommendations:
        top_names = ", ".join(item["name"] for item in recommendations[:3])
        reply = f"Here are the strongest matches based on your request and saved preferences: {top_names}."
    else:
        reply = "I could not find a close match, so try broadening the cuisine, location, or budget filters."

    if live_context:
        reply = f"{reply} I also checked live web context for timing or trending clues."

    applied_filters = dict(filters)
    applied_filters["saved_search_radius"] = preferences.get("search_radius")

    for item in recommendations:
        item.pop("score", None)
        item.pop("matched_location", None)
        item.pop("price_sort", None)

    return {
        "reply": reply,
        "applied_filters": applied_filters,
        "recommendations": recommendations,
    }
