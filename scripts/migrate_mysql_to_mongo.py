from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend_shared.db import ensure_indexes, get_database
from backend_shared.ids import set_counter_value
from backend_shared.utils import utcnow

from app.database import SessionLocal
from app.models.favorite import Favorite
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.models.user import User, UserPreference


def _split_csv(value: str | None):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def migrate(drop_existing: bool):
    db = get_database()
    ensure_indexes()

    if drop_existing:
        for collection in (
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
            db[collection].delete_many({})

    session = SessionLocal()
    try:
        users = session.query(User).all()
        preferences = {item.user_id: item for item in session.query(UserPreference).all()}
        restaurants = session.query(Restaurant).all()
        reviews = session.query(Review).all()
        favorites = session.query(Favorite).all()

        for user in users:
            db.users.replace_one(
                {"id": user.id},
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "password_hash": user.password_hash,
                    "role": user.role.value if hasattr(user.role, "value") else str(user.role),
                    "phone_number": user.phone_number,
                    "about_me": user.about_me,
                    "city": user.city,
                    "state": user.state,
                    "country": user.country,
                    "languages": user.languages,
                    "gender": user.gender,
                    "profile_image_url": user.profile_image_url,
                    "restaurant_location": user.restaurant_location,
                    "created_at": user.created_at,
                },
                upsert=True,
            )

            preference = preferences.get(user.id)
            if preference:
                db.preferences.replace_one(
                    {"user_id": user.id},
                    {
                        "user_id": user.id,
                        "preferred_cuisines": _split_csv(preference.preferred_cuisines),
                        "price_range": preference.price_range,
                        "preferred_locations": _split_csv(preference.preferred_locations),
                        "search_radius": preference.search_radius,
                        "dietary_needs": _split_csv(preference.dietary_needs),
                        "ambiance_preferences": _split_csv(preference.ambiance_preferences),
                        "sort_preference": preference.sort_preference,
                        "created_at": preference.created_at,
                        "updated_at": preference.updated_at,
                    },
                    upsert=True,
                )

        for restaurant in restaurants:
            db.restaurants.replace_one(
                {"id": restaurant.id},
                {
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "cuisine_type": restaurant.cuisine_type,
                    "description": restaurant.description,
                    "address": restaurant.address,
                    "city": restaurant.city,
                    "state": restaurant.state,
                    "zip_code": restaurant.zip_code,
                    "price_tier": restaurant.price_tier,
                    "contact_phone": restaurant.contact_phone,
                    "hours_text": restaurant.hours_text,
                    "photo_url": restaurant.photo_url,
                    "amenities_text": restaurant.amenities_text,
                    "view_count": int(restaurant.view_count or 0),
                    "owner_id": restaurant.owner_id,
                    "created_by": restaurant.created_by,
                    "created_at": restaurant.created_at,
                },
                upsert=True,
            )

        for review in reviews:
            db.reviews.replace_one(
                {"id": review.id},
                {
                    "id": review.id,
                    "rating": review.rating,
                    "comment": review.comment,
                    "photo_url": review.photo_url,
                    "user_id": review.user_id,
                    "restaurant_id": review.restaurant_id,
                    "created_at": review.created_at,
                    "updated_at": review.updated_at,
                },
                upsert=True,
            )

        for favorite in favorites:
            db.favorites.replace_one(
                {"id": favorite.id},
                {
                    "id": favorite.id,
                    "user_id": favorite.user_id,
                    "restaurant_id": favorite.restaurant_id,
                    "created_at": favorite.created_at,
                },
                upsert=True,
            )

        activity_id = 0
        for restaurant in restaurants:
            activity_id += 1
            db.activity_logs.replace_one(
                {"id": activity_id},
                {
                    "id": activity_id,
                    "user_id": restaurant.created_by,
                    "event_type": "restaurant.created",
                    "restaurant_id": restaurant.id,
                    "review_id": None,
                    "favorite_id": None,
                    "metadata": {"restaurant_name": restaurant.name},
                    "created_at": restaurant.created_at,
                },
                upsert=True,
            )
            if restaurant.owner_id:
                activity_id += 1
                db.activity_logs.replace_one(
                    {"id": activity_id},
                    {
                        "id": activity_id,
                        "user_id": restaurant.owner_id,
                        "event_type": "restaurant.claimed",
                        "restaurant_id": restaurant.id,
                        "review_id": None,
                        "favorite_id": None,
                        "metadata": {"restaurant_name": restaurant.name},
                        "created_at": restaurant.created_at,
                    },
                    upsert=True,
                )

        for review in reviews:
            activity_id += 1
            db.activity_logs.replace_one(
                {"id": activity_id},
                {
                    "id": activity_id,
                    "user_id": review.user_id,
                    "event_type": "review.created",
                    "restaurant_id": review.restaurant_id,
                    "review_id": review.id,
                    "favorite_id": None,
                    "metadata": {"rating": review.rating},
                    "created_at": review.created_at,
                },
                upsert=True,
            )

        for favorite in favorites:
            activity_id += 1
            db.activity_logs.replace_one(
                {"id": activity_id},
                {
                    "id": activity_id,
                    "user_id": favorite.user_id,
                    "event_type": "favorite.added",
                    "restaurant_id": favorite.restaurant_id,
                    "review_id": None,
                    "favorite_id": favorite.id,
                    "metadata": {},
                    "created_at": favorite.created_at,
                },
                upsert=True,
            )

        set_counter_value(db, "users", max((user.id for user in users), default=0))
        set_counter_value(db, "restaurants", max((restaurant.id for restaurant in restaurants), default=0))
        set_counter_value(db, "reviews", max((review.id for review in reviews), default=0))
        set_counter_value(db, "favorites", max((favorite.id for favorite in favorites), default=0))
        set_counter_value(db, "activity_logs", activity_id)
        set_counter_value(db, "review_jobs", 0)

        print("Migration complete.")
        print(f"Users: {len(users)}")
        print(f"Preferences: {len(preferences)}")
        print(f"Restaurants: {len(restaurants)}")
        print(f"Reviews: {len(reviews)}")
        print(f"Favorites: {len(favorites)}")
        print(f"Activity logs: {activity_id}")
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Migrate Lab 1 MySQL data into Lab 2 MongoDB collections.")
    parser.add_argument("--drop-existing", action="store_true", help="Clear target MongoDB collections before migration.")
    args = parser.parse_args()
    migrate(drop_existing=args.drop_existing)


if __name__ == "__main__":
    main()
