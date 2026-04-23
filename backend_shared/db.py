from __future__ import annotations

from functools import lru_cache

from pymongo import ASCENDING, DESCENDING, MongoClient

from backend_shared.config import get_settings


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(settings.mongodb_url, tz_aware=False)


def get_database():
    settings = get_settings()
    return get_mongo_client()[settings.mongodb_database]


def ensure_indexes():
    db = get_database()

    db.users.create_index("id", unique=True)
    db.users.create_index("email", unique=True)

    db.preferences.create_index("user_id", unique=True)

    db.sessions.create_index("session_id", unique=True)
    db.sessions.create_index("expires_at", expireAfterSeconds=0)
    db.sessions.create_index([("user_id", ASCENDING), ("revoked_at", ASCENDING)])

    db.restaurants.create_index("id", unique=True)
    db.restaurants.create_index([("city", ASCENDING), ("cuisine_type", ASCENDING)])
    db.restaurants.create_index("created_by")
    db.restaurants.create_index("owner_id")

    db.reviews.create_index("id", unique=True)
    db.reviews.create_index([("restaurant_id", ASCENDING), ("created_at", DESCENDING)])
    db.reviews.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

    db.favorites.create_index("id", unique=True)
    db.favorites.create_index([("user_id", ASCENDING), ("restaurant_id", ASCENDING)], unique=True)

    db.review_jobs.create_index("id", unique=True)
    db.review_jobs.create_index("job_id", unique=True)
    db.review_jobs.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

    db.activity_logs.create_index("id", unique=True)
    db.activity_logs.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

    db.counters.create_index("name", unique=True)
