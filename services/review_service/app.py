from __future__ import annotations

import threading
import time

from fastapi import Depends, HTTPException

from backend_shared.auth import get_current_user
from backend_shared.config import get_settings
from backend_shared.db import get_database
from backend_shared.kafka_utils import create_consumer, publish_message
from backend_shared.query_helpers import fetch_reviews_with_authors
from backend_shared.review_jobs import create_review_job, update_review_job_status
from backend_shared.schemas import ReviewCreate, ReviewJobResponse, ReviewResponse, ReviewUpdate
from backend_shared.serializers import serialize_review_job
from backend_shared.service_factory import create_service_app

app = create_service_app(
    title="Lab 2 Review Service",
    description="Asynchronous review producer API with Kafka-backed job tracking.",
)

_stop_event = threading.Event()
_consumer_thread: threading.Thread | None = None


def _status_consumer_loop(stop_event: threading.Event):
    settings = get_settings()
    while not stop_event.is_set():
        try:
            consumer = create_consumer(settings.kafka_review_status_topic, group_id="review-status-updater")
            while not stop_event.is_set():
                batches = consumer.poll(timeout_ms=1000)
                for records in batches.values():
                    for record in records:
                        payload = record.value
                        update_review_job_status(
                            get_database(),
                            job_id=payload["job_id"],
                            status=payload["status"],
                            review_id=payload.get("review_id"),
                            error=payload.get("error"),
                            restaurant_id=payload.get("restaurant_id"),
                        )
            consumer.close()
        except Exception:
            time.sleep(3)


@app.on_event("startup")
def start_status_consumer():
    global _consumer_thread
    settings = get_settings()
    if not settings.review_status_consumer_enabled:
        return
    if _consumer_thread and _consumer_thread.is_alive():
        return
    _stop_event.clear()
    _consumer_thread = threading.Thread(target=_status_consumer_loop, args=(_stop_event,), daemon=True)
    _consumer_thread.start()


@app.on_event("shutdown")
def stop_status_consumer():
    _stop_event.set()


@app.get("/reviews/restaurant/{restaurant_id}", response_model=list[ReviewResponse])
def reviews_for_restaurant(restaurant_id: int):
    db = get_database()
    return [ReviewResponse(**review) for review in fetch_reviews_with_authors(db, restaurant_id)]


@app.post("/reviews/", response_model=ReviewJobResponse, status_code=202)
def create_review(payload: ReviewCreate, current_user: dict = Depends(get_current_user({"USER"}))):
    db = get_database()
    restaurant = db.restaurants.find_one({"id": payload.restaurant_id})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    job = create_review_job(
        db,
        user_id=current_user["id"],
        restaurant_id=payload.restaurant_id,
        operation="create",
        payload={
            "rating": payload.rating,
            "comment": payload.comment,
            "photo_url": payload.photo_url,
            "restaurant_id": payload.restaurant_id,
            "user_id": current_user["id"],
        },
    )
    settings = get_settings()
    publish_message(
        settings.kafka_review_created_topic,
        {
            "job_id": job["job_id"],
            "operation": "create",
            "user_id": current_user["id"],
            "restaurant_id": payload.restaurant_id,
            "payload": job["payload"],
        },
    )
    return ReviewJobResponse(**serialize_review_job(job))


@app.put("/reviews/{review_id}", response_model=ReviewJobResponse, status_code=202)
def update_review(review_id: int, payload: ReviewUpdate, current_user: dict = Depends(get_current_user({"USER"}))):
    db = get_database()
    review = db.reviews.find_one({"id": review_id})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if int(review["user_id"]) != int(current_user["id"]):
        raise HTTPException(status_code=403, detail="Not authorized to update")

    job = create_review_job(
        db,
        user_id=current_user["id"],
        restaurant_id=review["restaurant_id"],
        operation="update",
        payload={
            "review_id": review_id,
            "restaurant_id": review["restaurant_id"],
            "user_id": current_user["id"],
            "rating": payload.rating,
            "comment": payload.comment,
            "photo_url": payload.photo_url,
        },
    )
    settings = get_settings()
    publish_message(
        settings.kafka_review_updated_topic,
        {
            "job_id": job["job_id"],
            "operation": "update",
            "user_id": current_user["id"],
            "restaurant_id": review["restaurant_id"],
            "payload": job["payload"],
        },
    )
    return ReviewJobResponse(**serialize_review_job(job))


@app.delete("/reviews/{review_id}", response_model=ReviewJobResponse, status_code=202)
def delete_review(review_id: int, current_user: dict = Depends(get_current_user({"USER"}))):
    db = get_database()
    review = db.reviews.find_one({"id": review_id})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if int(review["user_id"]) != int(current_user["id"]):
        raise HTTPException(status_code=403, detail="Not authorized to delete")

    job = create_review_job(
        db,
        user_id=current_user["id"],
        restaurant_id=review["restaurant_id"],
        operation="delete",
        payload={
            "review_id": review_id,
            "restaurant_id": review["restaurant_id"],
            "user_id": current_user["id"],
        },
    )
    settings = get_settings()
    publish_message(
        settings.kafka_review_deleted_topic,
        {
            "job_id": job["job_id"],
            "operation": "delete",
            "user_id": current_user["id"],
            "restaurant_id": review["restaurant_id"],
            "payload": job["payload"],
        },
    )
    return ReviewJobResponse(**serialize_review_job(job))


@app.get("/review-jobs/{job_id}", response_model=ReviewJobResponse)
def review_job_status(job_id: str, current_user: dict = Depends(get_current_user())):
    db = get_database()
    review_job = db.review_jobs.find_one({"job_id": job_id})
    if not review_job:
        raise HTTPException(status_code=404, detail="Review job not found")
    if int(review_job["user_id"]) != int(current_user["id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    return ReviewJobResponse(**serialize_review_job(review_job))
