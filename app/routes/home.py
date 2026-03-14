from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models.restaurant import Restaurant
from app.models.review import Review

router = APIRouter(tags=["Home"])


@router.get("/home")
def public_home(db: Session = Depends(get_db)):

    # 🔥 Top Rated
    top_rated_query = (
        db.query(
            Restaurant.id,
            Restaurant.name,
            func.avg(Review.rating).label("average_rating")
        )
        .join(Review, Review.restaurant_id == Restaurant.id)
        .group_by(Restaurant.id)
        .order_by(desc("average_rating"))
        .limit(5)
        .all()
    )

    top_rated = [
        {
            "id": r.id,
            "name": r.name,
            "average_rating": float(r.average_rating) if r.average_rating else 0
        }
        for r in top_rated_query
    ]

    # 🔥 Most Reviewed
    most_reviewed_query = (
        db.query(
            Restaurant.id,
            Restaurant.name,
            func.count(Review.id).label("review_count")
        )
        .join(Review, Review.restaurant_id == Restaurant.id)
        .group_by(Restaurant.id)
        .order_by(desc("review_count"))
        .limit(5)
        .all()
    )

    most_reviewed = [
        {
            "id": r.id,
            "name": r.name,
            "review_count": r.review_count
        }
        for r in most_reviewed_query
    ]

    # 🔥 Recently Added
    recent_query = (
        db.query(Restaurant)
        .order_by(Restaurant.created_at.desc())
        .limit(5)
        .all()
    )

    recent = [
        {
            "id": r.id,
            "name": r.name,
            "city": r.city,
            "price_tier": r.price_tier
        }
        for r in recent_query
    ]

    return {
        "top_rated": top_rated,
        "most_reviewed": most_reviewed,
        "recent_restaurants": recent
    }