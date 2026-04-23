from __future__ import annotations

import time

from backend_shared.activity import record_activity
from backend_shared.config import get_settings
from backend_shared.db import ensure_indexes, get_database
from backend_shared.ids import get_next_id
from backend_shared.kafka_utils import create_consumer, publish_message
from backend_shared.utils import utcnow


def _publish_status(*, job_id: str, status: str, restaurant_id: int | None = None, review_id: int | None = None, error: str | None = None):
    settings = get_settings()
    publish_message(
        settings.kafka_review_status_topic,
        {
            "job_id": job_id,
            "status": status,
            "restaurant_id": restaurant_id,
            "review_id": review_id,
            "error": error,
        },
    )


def _handle_create(db, message: dict):
    payload = message["payload"]
    restaurant = db.restaurants.find_one({"id": payload["restaurant_id"]})
    if not restaurant:
        raise ValueError("Restaurant not found")

    review_id = get_next_id(db, "reviews")
    review = {
        "id": review_id,
        "restaurant_id": payload["restaurant_id"],
        "rating": payload["rating"],
        "comment": payload.get("comment"),
        "photo_url": payload.get("photo_url"),
        "user_id": payload["user_id"],
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    db.reviews.insert_one(review)
    record_activity(
        db,
        user_id=payload["user_id"],
        event_type="review.created",
        restaurant_id=payload["restaurant_id"],
        review_id=review_id,
        metadata={"rating": payload["rating"]},
    )
    return review_id


def _handle_update(db, message: dict):
    payload = message["payload"]
    review = db.reviews.find_one({"id": payload["review_id"]})
    if not review:
        raise ValueError("Review not found")

    update_fields = {"updated_at": utcnow()}
    for field in ("rating", "comment", "photo_url"):
        if payload.get(field) is not None:
            update_fields[field] = payload[field]
    db.reviews.update_one({"id": payload["review_id"]}, {"$set": update_fields})
    record_activity(
        db,
        user_id=payload["user_id"],
        event_type="review.updated",
        restaurant_id=payload["restaurant_id"],
        review_id=payload["review_id"],
        metadata={"updated_fields": sorted(update_fields.keys())},
    )
    return int(payload["review_id"])


def _handle_delete(db, message: dict):
    payload = message["payload"]
    review = db.reviews.find_one({"id": payload["review_id"]})
    if not review:
        raise ValueError("Review not found")

    db.reviews.delete_one({"id": payload["review_id"]})
    record_activity(
        db,
        user_id=payload["user_id"],
        event_type="review.deleted",
        restaurant_id=payload["restaurant_id"],
        review_id=payload["review_id"],
    )
    return int(payload["review_id"])


def run_worker():
    ensure_indexes()
    settings = get_settings()

    while True:
        try:
            consumer = create_consumer(
                settings.kafka_review_created_topic,
                settings.kafka_review_updated_topic,
                settings.kafka_review_deleted_topic,
                group_id="review-worker",
            )

            while True:
                batches = consumer.poll(timeout_ms=1000)
                db = get_database()
                for records in batches.values():
                    for record in records:
                        message = record.value
                        job_id = message["job_id"]
                        restaurant_id = message["restaurant_id"]
                        _publish_status(job_id=job_id, status="processing", restaurant_id=restaurant_id)
                        try:
                            if record.topic == settings.kafka_review_created_topic:
                                review_id = _handle_create(db, message)
                            elif record.topic == settings.kafka_review_updated_topic:
                                review_id = _handle_update(db, message)
                            else:
                                review_id = _handle_delete(db, message)
                            _publish_status(
                                job_id=job_id,
                                status="completed",
                                restaurant_id=restaurant_id,
                                review_id=review_id,
                            )
                        except Exception as exc:
                            _publish_status(
                                job_id=job_id,
                                status="failed",
                                restaurant_id=restaurant_id,
                                error=str(exc),
                            )
        except Exception:
            time.sleep(3)


if __name__ == "__main__":
    run_worker()
