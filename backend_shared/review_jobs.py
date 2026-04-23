from __future__ import annotations

from backend_shared.ids import get_next_id
from backend_shared.utils import utcnow


def create_review_job(db, *, user_id: int, restaurant_id: int, operation: str, payload: dict):
    job_number = get_next_id(db, "review_jobs")
    job_id = f"review-job-{job_number}"
    document = {
        "id": job_number,
        "job_id": job_id,
        "user_id": user_id,
        "restaurant_id": restaurant_id,
        "operation": operation,
        "payload": payload,
        "status": "queued",
        "review_id": payload.get("review_id"),
        "error": None,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    db.review_jobs.insert_one(document)
    return document


def update_review_job_status(db, *, job_id: str, status: str, review_id: int | None = None, error: str | None = None, restaurant_id: int | None = None):
    update = {
        "status": status,
        "updated_at": utcnow(),
    }
    if review_id is not None:
        update["review_id"] = review_id
    if restaurant_id is not None:
        update["restaurant_id"] = restaurant_id
    update["error"] = error
    db.review_jobs.update_one({"job_id": job_id}, {"$set": update})
