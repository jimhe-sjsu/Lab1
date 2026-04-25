#!/usr/bin/env python3
"""Scale Lab 2 MongoDB data for load testing.

The script grows the current MongoDB database to target counts without relying
on the old MySQL schema. Existing documents are preserved by default.
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pymongo import UpdateOne

from backend_shared.auth import hash_password
from backend_shared.db import ensure_indexes, get_database
from backend_shared.ids import set_counter_value
from backend_shared.utils import utcnow

DEFAULT_PASSWORD = "Password123!"
BATCH_SIZE = 1000

CUISINES = [
    "Indian",
    "Italian",
    "Chinese",
    "Mexican",
    "Thai",
    "American",
    "Mediterranean",
    "Japanese",
    "Korean",
    "French",
    "Vietnamese",
    "Greek",
]

CITIES = [
    ("Palo Alto", "94301"),
    ("San Jose", "95112"),
    ("Sunnyvale", "94086"),
    ("Santa Clara", "95050"),
    ("Mountain View", "94041"),
    ("Cupertino", "95014"),
    ("Fremont", "94538"),
    ("Milpitas", "95035"),
    ("Redwood City", "94063"),
    ("Foster City", "94404"),
]

AMENITIES = [
    "wifi",
    "outdoor seating",
    "delivery",
    "takeout",
    "parking",
    "family-friendly",
    "vegan options",
    "reservations",
    "quiet",
    "late night",
]

COMMENTS = [
    "Reliable neighborhood spot with quick service.",
    "Good flavors and a comfortable dining room.",
    "Busy during dinner but worth the wait.",
    "Fresh ingredients and friendly staff.",
    "Solid option for casual meals.",
    "The menu has enough variety for groups.",
    "Clean space with consistent food quality.",
    "Great value for the portion size.",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grow Lab 2 MongoDB collections to load-test scale.")
    parser.add_argument("--users", type=int, default=10000, help="Target total users, including existing users.")
    parser.add_argument("--restaurants", type=int, default=10000, help="Target total restaurants, including existing restaurants.")
    parser.add_argument("--reviews", type=int, default=10000, help="Target total reviews, including existing reviews.")
    parser.add_argument("--seed", type=int, default=236, help="Random seed for deterministic generated data.")
    parser.add_argument("--drop-existing", action="store_true", help="Clear generated/runtime collections before seeding.")
    parser.add_argument("--default-password", default=DEFAULT_PASSWORD, help="Password used for generated users.")
    return parser.parse_args()


def bulk_write(collection, operations: list[UpdateOne]):
    if operations:
        collection.bulk_write(operations, ordered=False)


def next_id_start(db, collection_name: str) -> int:
    max_doc = db[collection_name].find_one(sort=[("id", -1)], projection={"id": 1})
    return int(max_doc["id"]) + 1 if max_doc else 1


def generate_users(db, target_count: int, password_hash: str):
    existing = db.users.count_documents({})
    to_create = max(0, target_count - existing)
    if to_create == 0:
        return []

    start_id = next_id_start(db, "users")
    operations: list[UpdateOne] = []
    created_ids: list[int] = []
    now = utcnow()

    for offset in range(to_create):
        user_id = start_id + offset
        role = "OWNER" if offset % 10 == 0 else "USER"
        city, _ = CITIES[offset % len(CITIES)]
        cuisine = CUISINES[offset % len(CUISINES)]
        document = {
            "id": user_id,
            "name": f"Scale {role.title()} {user_id}",
            "email": f"scale-{role.lower()}-{user_id}@example.com",
            "password_hash": password_hash,
            "role": role,
            "phone_number": f"408-555-{user_id % 10000:04d}",
            "about_me": f"Generated {role.lower()} account for Lab 2 load testing.",
            "city": city,
            "state": "CA",
            "country": "United States",
            "languages": "English",
            "gender": None,
            "profile_image_url": None,
            "restaurant_location": city if role == "OWNER" else None,
            "created_at": now - timedelta(minutes=offset % 1440),
        }
        operations.append(UpdateOne({"id": user_id}, {"$set": document}, upsert=True))
        created_ids.append(user_id)

        if len(operations) >= BATCH_SIZE:
            bulk_write(db.users, operations)
            operations = []

    bulk_write(db.users, operations)
    return created_ids


def generate_preferences(db, user_ids: list[int]):
    operations: list[UpdateOne] = []
    now = utcnow()
    for index, user_id in enumerate(user_ids):
        if db.users.find_one({"id": user_id, "role": "USER"}, {"id": 1}) is None:
            continue
        document = {
            "user_id": user_id,
            "preferred_cuisines": [CUISINES[index % len(CUISINES)], CUISINES[(index + 3) % len(CUISINES)]],
            "price_range": ["$", "$$", "$$$", "$$$$"][index % 4],
            "preferred_locations": [CITIES[index % len(CITIES)][0]],
            "search_radius": [5, 10, 15, 25, 50][index % 5],
            "dietary_needs": ["vegetarian"] if index % 7 == 0 else [],
            "ambiance_preferences": [AMENITIES[index % len(AMENITIES)]],
            "sort_preference": "rating",
            "created_at": now,
            "updated_at": now,
        }
        operations.append(UpdateOne({"user_id": user_id}, {"$set": document}, upsert=True))
        if len(operations) >= BATCH_SIZE:
            bulk_write(db.preferences, operations)
            operations = []

    bulk_write(db.preferences, operations)


def generate_restaurants(db, target_count: int):
    existing = db.restaurants.count_documents({})
    to_create = max(0, target_count - existing)
    if to_create == 0:
        return []

    owner_ids = [doc["id"] for doc in db.users.find({"role": "OWNER"}, {"id": 1}).sort("id", 1)]
    if not owner_ids:
        raise RuntimeError("Need at least one OWNER user before creating restaurants.")

    start_id = next_id_start(db, "restaurants")
    operations: list[UpdateOne] = []
    created_ids: list[int] = []
    now = utcnow()

    for offset in range(to_create):
        restaurant_id = start_id + offset
        city, zip_code = CITIES[offset % len(CITIES)]
        cuisine = CUISINES[offset % len(CUISINES)]
        owner_id = owner_ids[offset % len(owner_ids)]
        document = {
            "id": restaurant_id,
            "name": f"Scale {cuisine} Kitchen {restaurant_id:05d}",
            "cuisine_type": cuisine,
            "description": f"{cuisine} restaurant generated for Lab 2 load testing.",
            "address": f"{100 + (offset % 9000)} Scale Avenue",
            "city": city,
            "state": "CA",
            "zip_code": zip_code,
            "price_tier": ["$", "$$", "$$$", "$$$$"][offset % 4],
            "contact_phone": f"408-777-{offset % 10000:04d}",
            "hours_text": "Mon-Sun 10:00 AM - 10:00 PM",
            "photo_url": f"https://picsum.photos/seed/lab2-scale-restaurant-{restaurant_id}/1200/800",
            "amenities_text": ",".join(random.sample(AMENITIES, k=3)),
            "view_count": int((offset * 13) % 5000),
            "owner_id": owner_id if offset % 3 != 0 else None,
            "created_by": owner_id,
            "created_at": now - timedelta(minutes=offset % 10080),
        }
        operations.append(UpdateOne({"id": restaurant_id}, {"$set": document}, upsert=True))
        created_ids.append(restaurant_id)

        if len(operations) >= BATCH_SIZE:
            bulk_write(db.restaurants, operations)
            operations = []

    bulk_write(db.restaurants, operations)
    return created_ids


def generate_reviews(db, target_count: int):
    existing = db.reviews.count_documents({})
    to_create = max(0, target_count - existing)
    if to_create == 0:
        return []

    user_ids = [doc["id"] for doc in db.users.find({"role": "USER"}, {"id": 1}).sort("id", 1)]
    restaurant_ids = [doc["id"] for doc in db.restaurants.find({}, {"id": 1}).sort("id", 1)]
    if not user_ids or not restaurant_ids:
        raise RuntimeError("Need USER accounts and restaurants before creating reviews.")

    start_id = next_id_start(db, "reviews")
    operations: list[UpdateOne] = []
    activity_operations: list[UpdateOne] = []
    created_ids: list[int] = []
    activity_start = next_id_start(db, "activity_logs")
    now = utcnow()

    for offset in range(to_create):
        review_id = start_id + offset
        user_id = user_ids[offset % len(user_ids)]
        restaurant_id = restaurant_ids[(offset * 17) % len(restaurant_ids)]
        created_at = now - timedelta(minutes=offset % 43200)
        review = {
            "id": review_id,
            "rating": 1 + (offset % 5),
            "comment": COMMENTS[offset % len(COMMENTS)],
            "photo_url": None,
            "user_id": user_id,
            "restaurant_id": restaurant_id,
            "created_at": created_at,
            "updated_at": created_at,
        }
        operations.append(UpdateOne({"id": review_id}, {"$set": review}, upsert=True))
        activity_operations.append(
            UpdateOne(
                {"id": activity_start + offset},
                {
                    "$set": {
                        "id": activity_start + offset,
                        "user_id": user_id,
                        "event_type": "review.created",
                        "restaurant_id": restaurant_id,
                        "review_id": review_id,
                        "favorite_id": None,
                        "metadata": {"rating": review["rating"], "source": "scale_seed"},
                        "created_at": created_at,
                    }
                },
                upsert=True,
            )
        )
        created_ids.append(review_id)

        if len(operations) >= BATCH_SIZE:
            bulk_write(db.reviews, operations)
            bulk_write(db.activity_logs, activity_operations)
            operations = []
            activity_operations = []

    bulk_write(db.reviews, operations)
    bulk_write(db.activity_logs, activity_operations)
    return created_ids


def refresh_counters(db):
    for collection_name in ("users", "restaurants", "reviews", "favorites", "review_jobs", "activity_logs"):
        document = db[collection_name].find_one(sort=[("id", -1)], projection={"id": 1})
        set_counter_value(db, collection_name, int(document["id"]) if document else 0)


def find_generated_account(db, role: str):
    prefix = f"^scale-{role.lower()}-"
    return db.users.find_one(
        {"role": role, "email": {"$regex": prefix}},
        {"_id": 0, "id": 1, "email": 1},
        sort=[("id", 1)],
    )


def clear_runtime_collections(db):
    for collection_name in (
        "users",
        "preferences",
        "sessions",
        "restaurants",
        "reviews",
        "favorites",
        "activity_logs",
        "review_jobs",
        "counters",
    ):
        db[collection_name].delete_many({})


def main():
    args = parse_args()
    random.seed(args.seed)

    if min(args.users, args.restaurants, args.reviews) < 1:
        raise SystemExit("Targets must all be positive integers.")

    db = get_database()
    ensure_indexes()

    if args.drop_existing:
        clear_runtime_collections(db)

    password_hash = hash_password(args.default_password)
    created_user_ids = generate_users(db, args.users, password_hash)
    if created_user_ids:
        generate_preferences(db, created_user_ids)

    generate_restaurants(db, args.restaurants)
    generate_reviews(db, args.reviews)
    refresh_counters(db)

    counts = {
        "users": db.users.count_documents({}),
        "preferences": db.preferences.count_documents({}),
        "restaurants": db.restaurants.count_documents({}),
        "reviews": db.reviews.count_documents({}),
        "activity_logs": db.activity_logs.count_documents({}),
        "review_jobs": db.review_jobs.count_documents({}),
    }

    print("Mongo scale seed complete.")
    for name, count in counts.items():
        print(f"{name}: {count}")
    print(f"Generated user password: {args.default_password}")
    reviewer = find_generated_account(db, "USER")
    owner = find_generated_account(db, "OWNER")
    if reviewer:
        print(f"Example generated reviewer: {reviewer['email']}")
    if owner:
        print(f"Example generated owner: {owner['email']}")


if __name__ == "__main__":
    main()
