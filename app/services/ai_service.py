import json
import os
import re
from typing import Any, Dict, List, Optional

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

PRICE_SYMBOLS = ["$", "$$", "$$$", "$$$$"]
PRICE_HINTS = [
    "cheap",
    "budget",
    "affordable",
    "mid-range",
    "mid range",
    "expensive",
    "premium",
    "luxury",
    "high priced",
    "high-price",
    "fine dining",
]
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
LIVE_CONTEXT_TERMS = [
    "open now",
    "hours",
    "today",
    "tonight",
    "event",
    "trending",
    "special",
    "this weekend",
    "busy",
    "crowded",
    "current",
]

_EMPTY_PREFS = {
    "preferred_cuisines": [],
    "price_range": None,
    "preferred_locations": [],
    "search_radius": None,
    "dietary_needs": [],
    "ambiance_preferences": [],
    "sort_preference": None,
}


_NATIONALITY_PHRASES = [
    r"\bi\s*am\s+an?\s+indian\b",
    r"\bi'?m\s+an?\s+indian\b",
    r"\bas\s+i\s*am\s+an?\s+indian\b",
    r"\bas\s+i'?m\s+an?\s+indian\b",
]


SPECIFIC_RESTAURANT_PATTERNS = [
    r"recommend\s+(?P<name>[a-z0-9'&.\- ]{2,60})",
    r"about\s+(?P<name>[a-z0-9'&.\- ]{2,60})",
    r"is\s+(?P<name>[a-z0-9'&.\- ]{2,60})\s+good",
    r"how\s+is\s+(?P<name>[a-z0-9'&.\- ]{2,60})",
    r"thoughts\s+on\s+(?P<name>[a-z0-9'&.\- ]{2,60})",
]


def _csv_to_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]



def load_user_preferences(db: Session, user_id: int) -> Dict[str, Any]:
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        return dict(_EMPTY_PREFS)

    return {
        "preferred_cuisines": _csv_to_list(pref.preferred_cuisines),
        "price_range": pref.price_range,
        "preferred_locations": _csv_to_list(pref.preferred_locations),
        "search_radius": pref.search_radius,
        "dietary_needs": _csv_to_list(pref.dietary_needs),
        "ambiance_preferences": _csv_to_list(pref.ambiance_preferences),
        "sort_preference": pref.sort_preference,
    }



def _get_llm():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            api_key=api_key,
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            temperature=0.2,
        )
    except Exception:
        return None



def _extract_json(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except Exception:
        return {}



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



def _extract_by_keywords(text: str, keywords: List[str]) -> List[str]:
    lowered = text.lower()
    return [keyword for keyword in keywords if keyword in lowered]



def _normalize_price_hints(text: str) -> List[str]:
    lowered = text.lower()
    hints = [hint for hint in PRICE_HINTS if hint in lowered]
    hints.extend([symbol for symbol in PRICE_SYMBOLS if symbol in text])
    return list(dict.fromkeys(hints))



def _infer_sort_preference(text: str) -> Optional[str]:
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



def _fallback_specific_restaurant_name(text: str) -> Optional[str]:
    lowered = text.lower()
    for pattern in SPECIFIC_RESTAURANT_PATTERNS:
        match = re.search(pattern, lowered)
        if match:
            name = match.group("name")
            name = re.split(r"\b(?:as|because|for|with|near|in)\b", name)[0].strip(" ?!.,")
            if name:
                return " ".join(part.capitalize() for part in name.split())
    return None



def _fallback_parse_filters(message: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    history_text = " ".join(
        item.get("content", "") for item in conversation_history[-6:] if item.get("role") == "user"
    )
    combined = f"{history_text} {message}".strip()
    lowered = combined.lower()

    cuisines = _extract_by_keywords(lowered, CUISINE_KEYWORDS)
    if "indian" in cuisines:
        asks_for_indian_food = any(
            phrase in lowered
            for phrase in ["indian food", "indian restaurant", "indian cuisine", "want indian", "like indian"]
        )
        is_identity_statement = any(re.search(pattern, lowered) for pattern in _NATIONALITY_PHRASES)
        if is_identity_statement and not asks_for_indian_food:
            cuisines = [item for item in cuisines if item != "indian"]

    ambiance = _extract_by_keywords(lowered, AMBIANCE_KEYWORDS)
    occasion = _extract_by_keywords(lowered, OCCASION_KEYWORDS)
    dietary = _extract_by_keywords(lowered, DIETARY_KEYWORDS)
    keyword = None
    keyword_candidates = [item for item in ambiance if item not in {"family", "family-friendly", "date"}]
    if keyword_candidates:
        keyword = keyword_candidates[0]

    return {
        "restaurant_name": _fallback_specific_restaurant_name(message),
        "cuisines": cuisines,
        "price_hints": _normalize_price_hints(combined),
        "dietary": dietary,
        "ambiance": ambiance,
        "occasion": occasion,
        "location_terms": _extract_location_terms(combined),
        "keyword": keyword,
        "sort_preference": _infer_sort_preference(combined),
        "requires_live_context": any(term in lowered for term in LIVE_CONTEXT_TERMS),
    }



def _merge_list_values(primary: List[str], secondary: List[str]) -> List[str]:
    items: List[str] = []
    for source in (primary or [], secondary or []):
        for value in source:
            if value and value not in items:
                items.append(value)
    return items



def _parse_with_openai(message: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    llm = _get_llm()
    if llm is None:
        return {}

    history_text = "\n".join(
        f"{item.get('role', 'user')}: {item.get('content', '')}" for item in conversation_history[-8:]
    )
    prompt = PromptTemplate.from_template(
        """
You extract restaurant search intent for a Yelp-like assistant.
Return strict JSON only with these keys:
restaurant_name, cuisines, price_hints, dietary, ambiance, occasion, location_terms, keyword, sort_preference, requires_live_context.

Rules:
- If the user mentions a specific place like 'Do you recommend La Barre?', set restaurant_name to that place.
- Do NOT treat nationality or ethnicity as cuisine preference unless the user explicitly asks for that food.
  Example: 'I'm Indian' does not mean the user wants Indian food.
- price_hints should contain symbols like $, $$, $$$, $$$$ or hints like cheap, budget, affordable, mid-range, expensive, premium, luxury, high priced.
- sort_preference must be one of: rating, popularity, price, distance, null.
- keyword should be a short amenities/features phrase only if clearly requested.
- location_terms should contain city, zip, area names if present.
- requires_live_context should be true when the user asks about current hours, open now, today, tonight, specials, events, trending restaurants, or a specific restaurant that would benefit from live lookup.

Conversation history:
{history}

Latest user message:
{message}
""".strip()
    )

    try:
        response = llm.invoke(prompt.format(history=history_text or "none", message=message))
        content = response.content if hasattr(response, "content") else str(response)
        data = _extract_json(content)
        if isinstance(data, dict):
            return data
    except Exception:
        return {}

    return {}



def parse_filters(message: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    fallback = _fallback_parse_filters(message, conversation_history)
    llm_result = _parse_with_openai(message, conversation_history)

    merged = {
        "restaurant_name": llm_result.get("restaurant_name") or fallback.get("restaurant_name"),
        "cuisines": _merge_list_values(llm_result.get("cuisines", []), fallback.get("cuisines", [])),
        "price_hints": _merge_list_values(llm_result.get("price_hints", []), fallback.get("price_hints", [])),
        "dietary": _merge_list_values(llm_result.get("dietary", []), fallback.get("dietary", [])),
        "ambiance": _merge_list_values(llm_result.get("ambiance", []), fallback.get("ambiance", [])),
        "occasion": _merge_list_values(llm_result.get("occasion", []), fallback.get("occasion", [])),
        "location_terms": _merge_list_values(llm_result.get("location_terms", []), fallback.get("location_terms", [])),
        "keyword": llm_result.get("keyword") or fallback.get("keyword"),
        "sort_preference": llm_result.get("sort_preference") or fallback.get("sort_preference"),
        "requires_live_context": bool(llm_result.get("requires_live_context") or fallback.get("requires_live_context")),
    }

    return merged



def _price_from_hints(hints: List[str], preference_price: Optional[str]) -> Optional[str]:
    for symbol in ["$$$$", "$$$", "$$", "$"]:
        if symbol in hints:
            return symbol

    hint_map = {
        "cheap": "$",
        "budget": "$",
        "affordable": "$$",
        "mid range": "$$",
        "mid-range": "$$",
        "expensive": "$$$",
        "high priced": "$$$",
        "premium": "$$$$",
        "luxury": "$$$$",
        "fine dining": "$$$$",
    }
    for hint in hints:
        if hint in hint_map:
            return hint_map[hint]

    return preference_price



def _price_sort_value(price_tier: Optional[str]) -> int:
    mapping = {"$": 1, "$$": 2, "$$$": 3, "$$$$": 4}
    return mapping.get(price_tier or "$$", 2)



def _location_blob(restaurant: Restaurant) -> str:
    return " ".join(
        [
            restaurant.address or "",
            restaurant.city or "",
            restaurant.state or "",
            restaurant.zip_code or "",
        ]
    ).lower()



def _fetch_live_context(message: str, filters: Dict[str, Any], preferences: Dict[str, Any]) -> str:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return ""

    should_search = filters.get("requires_live_context") or bool(filters.get("restaurant_name"))
    if not should_search:
        return ""

    query_parts = []
    if filters.get("restaurant_name"):
        query_parts.append(str(filters["restaurant_name"]))
        query_parts.append("restaurant")
    else:
        query_parts.append(message)

    if filters.get("location_terms"):
        query_parts.append(str(filters["location_terms"][0]))
    elif preferences.get("preferred_locations"):
        query_parts.append(str(preferences["preferred_locations"][0]))

    tavily_query = " ".join(part for part in query_parts if part).strip()
    if not tavily_query:
        return ""

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        result = client.search(
            tavily_query,
            max_results=3,
            include_answer=True,
            search_depth="basic",
        )

        snippets: List[str] = []
        answer = result.get("answer")
        if isinstance(answer, str) and answer.strip():
            snippets.append(answer.strip())

        for item in result.get("results", [])[:3]:
            content = item.get("content") or ""
            if content:
                snippets.append(content.strip())

        combined = " ".join(snippets)
        return combined[:600]
    except Exception:
        return ""



def _rank_restaurants(rows: List[Any], filters: Dict[str, Any], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
    ranked: List[Dict[str, Any]] = []

    explicit_cuisines = [item.lower() for item in filters.get("cuisines", [])]
    preference_cuisines = [item.lower() for item in preferences.get("preferred_cuisines", [])]
    desired_price = _price_from_hints(filters.get("price_hints", []), preferences.get("price_range"))
    location_terms = [
        item.lower() for item in (filters.get("location_terms", []) or preferences.get("preferred_locations", []))
    ]
    dietary_terms = [item.lower() for item in _merge_list_values(filters.get("dietary", []), preferences.get("dietary_needs", []))]
    ambiance_terms = [item.lower() for item in _merge_list_values(filters.get("ambiance", []), preferences.get("ambiance_preferences", []))]
    occasion_terms = [item.lower() for item in filters.get("occasion", [])]
    specific_name = (filters.get("restaurant_name") or "").lower().strip()
    search_radius = preferences.get("search_radius")

    for restaurant, avg_rating, review_count in rows:
        reasons: List[str] = []
        score = float(avg_rating or 0) * 1.7 + min(int(review_count or 0), 80) * 0.05
        cuisine_text = (restaurant.cuisine_type or "").lower()
        name_text = (restaurant.name or "").lower()
        text_blob = " ".join(
            [
                restaurant.name or "",
                restaurant.description or "",
                restaurant.amenities_text or "",
                restaurant.hours_text or "",
                _location_blob(restaurant),
            ]
        ).lower()
        matched_location = False

        if specific_name:
            if specific_name == name_text:
                score += 7.0
                reasons.append("exact restaurant match")
            elif specific_name in name_text:
                score += 5.5
                reasons.append("matches the restaurant you asked about")

        if explicit_cuisines and any(cuisine in cuisine_text for cuisine in explicit_cuisines):
            score += 2.8
            reasons.append("matches your cuisine query")
        elif preference_cuisines and any(cuisine in cuisine_text for cuisine in preference_cuisines):
            score += 1.5
            reasons.append("matches your saved cuisine preference")

        if desired_price and restaurant.price_tier == desired_price:
            score += 1.4
            reasons.append("fits your price range")

        if location_terms:
            matched_location = any(term in text_blob for term in location_terms)
            if matched_location:
                score += 1.3
                if search_radius:
                    reasons.append(f"fits your preferred area within about {search_radius} miles")
                else:
                    reasons.append("aligns with your preferred area")

        if dietary_terms and any(term in text_blob or term in cuisine_text for term in dietary_terms):
            score += 1.5
            reasons.append("supports your dietary needs")

        if ambiance_terms and any(term in text_blob for term in ambiance_terms):
            score += 1.2
            reasons.append("matches the atmosphere you asked for")

        if occasion_terms:
            if any(term in occasion_terms for term in ["anniversary", "date"]):
                if any(term in text_blob for term in ["romantic", "fine dining", "outdoor", "cozy"]):
                    score += 1.2
                    reasons.append("fits a special-occasion dinner")
            elif any(term in occasion_terms for term in ["breakfast", "brunch", "lunch", "dinner", "tonight"]):
                if restaurant.hours_text:
                    score += 0.6
                    reasons.append("looks like a good timing match")

        keyword = (filters.get("keyword") or "").lower()
        if keyword and keyword in text_blob:
            score += 1.1
            reasons.append("matches requested features")

        ranked.append(
            {
                "id": restaurant.id,
                "name": restaurant.name,
                "cuisine": restaurant.cuisine_type,
                "average_rating": round(float(avg_rating or 0), 2),
                "review_count": int(review_count or 0),
                "price_tier": restaurant.price_tier or "$$",
                "reason": "; ".join(reasons[:2]) if reasons else "high overall rating and solid review volume",
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
        ranked.sort(key=lambda item: (item["score"], item["average_rating"]), reverse=True)

    return ranked[:5]



def _build_reply_with_openai(
    message: str,
    recommendations: List[Dict[str, Any]],
    filters: Dict[str, Any],
    preferences: Dict[str, Any],
    live_context: str,
) -> str:
    if not recommendations:
        return "I could not find a close match, so try broadening the cuisine, location, or budget filters."

    llm = _get_llm()
    if llm is None:
        return _build_fallback_reply(recommendations, filters, preferences, live_context)

    prompt = PromptTemplate.from_template(
        """
You are a warm restaurant recommendation assistant.
Write a concise, conversational reply in 3 to 5 sentences.

Rules:
- If the user asked about a specific restaurant, answer that first.
- Use only the provided restaurant data and live context summary.
- Do not invent hours, events, or facts.
- Mention 2 or 3 restaurants at most.
- Explain why each one fits.
- If live_context is empty, do not mention web search.

User message:
{message}

Extracted filters:
{filters}

Saved preferences:
{preferences}

Recommendations JSON:
{recommendations}

Live context summary:
{live_context}
""".strip()
    )

    try:
        response = llm.invoke(
            prompt.format(
                message=message,
                filters=json.dumps(filters, ensure_ascii=False),
                preferences=json.dumps(preferences, ensure_ascii=False),
                recommendations=json.dumps(recommendations[:3], ensure_ascii=False),
                live_context=live_context or "",
            )
        )
        content = response.content if hasattr(response, "content") else str(response)
        if isinstance(content, str) and content.strip():
            return content.strip()
    except Exception:
        pass

    return _build_fallback_reply(recommendations, filters, preferences, live_context)



def _build_fallback_reply(
    recommendations: List[Dict[str, Any]],
    filters: Dict[str, Any],
    preferences: Dict[str, Any],
    live_context: str,
) -> str:
    if not recommendations:
        return "I could not find a close match, so try broadening the cuisine, location, or budget filters."

    top = recommendations[:3]
    if filters.get("restaurant_name"):
        first = top[0]
        reply = (
            f"{first['name']} looks like a solid option: it has a {first['average_rating']:.1f} star average, "
            f"is priced at {first['price_tier']}, and {first['reason']}."
        )
        if len(top) > 1:
            reply += " If you want backups, I would also consider " + ", ".join(item["name"] for item in top[1:3]) + "."
    else:
        highlights = [
            f"{item['name']} ({item['average_rating']:.1f} star, {item['price_tier']}) - {item['reason']}"
            for item in top
        ]
        reply = "Here are my best matches: " + " | ".join(highlights) + "."

    if preferences.get("search_radius") and preferences.get("preferred_locations"):
        reply += (
            f" I also used your saved location preferences around {', '.join(preferences['preferred_locations'][:2])} "
            f"with a radius of about {preferences['search_radius']} miles."
        )

    if live_context:
        reply += " I also checked live web context for timing, current hours, or trending clues."

    return reply



def _base_query(db: Session):
    return (
        db.query(
            Restaurant,
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("review_count"),
        )
        .outerjoin(Review, Review.restaurant_id == Restaurant.id)
    )



def _apply_filters(query, filters: Dict[str, Any], preferences: Dict[str, Any]):
    cuisines = filters.get("cuisines", []) or preferences.get("preferred_cuisines", [])
    if cuisines:
        query = query.filter(or_(*[Restaurant.cuisine_type.ilike(f"%{cuisine}%") for cuisine in cuisines]))

    desired_price = _price_from_hints(filters.get("price_hints", []), preferences.get("price_range"))
    if desired_price:
        query = query.filter(Restaurant.price_tier == desired_price)

    location_terms = filters.get("location_terms", []) or preferences.get("preferred_locations", [])
    if location_terms:
        clauses = []
        for term in location_terms:
            clauses.extend(
                [
                    Restaurant.city.ilike(f"%{term}%"),
                    Restaurant.zip_code.ilike(f"%{term}%"),
                    Restaurant.address.ilike(f"%{term}%"),
                    Restaurant.state.ilike(f"%{term}%"),
                ]
            )
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

    return query



def find_recommendations(
    db: Session,
    current_user: User,
    message: str,
    conversation_history: List[Dict[str, str]],
) -> Dict[str, Any]:
    preferences = load_user_preferences(db, current_user.id)
    filters = parse_filters(message, conversation_history)

    if not filters.get("location_terms") and "near me" in message.lower() and preferences.get("preferred_locations"):
        filters["location_terms"] = list(preferences["preferred_locations"])

    rows: List[Any] = []

    specific_name = filters.get("restaurant_name")
    if specific_name:
        rows = (
            _base_query(db)
            .filter(Restaurant.name.ilike(f"%{specific_name}%"))
            .group_by(Restaurant.id)
            .all()
        )

    if not rows:
        rows = _apply_filters(_base_query(db), filters, preferences).group_by(Restaurant.id).all()

    if not rows:
        rows = _base_query(db).group_by(Restaurant.id).all()

    recommendations = _rank_restaurants(rows, filters, preferences)
    live_context = _fetch_live_context(message, filters, preferences)
    reply = _build_reply_with_openai(message, recommendations, filters, preferences, live_context)

    applied_filters = dict(filters)
    applied_filters["saved_search_radius"] = preferences.get("search_radius")
    applied_filters["saved_locations"] = preferences.get("preferred_locations")

    for item in recommendations:
        item.pop("score", None)
        item.pop("matched_location", None)
        item.pop("price_sort", None)

    return {
        "reply": reply,
        "applied_filters": applied_filters,
        "recommendations": recommendations,
    }
