from __future__ import annotations

from backend_shared.ids import get_next_id
from backend_shared.utils import utcnow


def record_activity(db, *, user_id: int, event_type: str, metadata: dict | None = None, restaurant_id: int | None = None, review_id: int | None = None, favorite_id: int | None = None):
    activity_id = get_next_id(db, "activity_logs")
    document = {
        "id": activity_id,
        "user_id": user_id,
        "event_type": event_type,
        "restaurant_id": restaurant_id,
        "review_id": review_id,
        "favorite_id": favorite_id,
        "metadata": metadata or {},
        "created_at": utcnow(),
    }
    db.activity_logs.insert_one(document)
    return document
