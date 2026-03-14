from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.restaurant import Restaurant
from app.models.review import Review
from sqlalchemy import func
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


@router.post("/recommend")
def recommend_restaurants(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Simple ranking-based recommendation system.
    """

    restaurants = db.query(
        Restaurant.id,
        Restaurant.name,
        Restaurant.cuisine_type,
        func.avg(Review.rating).label("avg_rating"),
        func.count(Review.id).label("review_count")
    ).join(
        Review, Review.restaurant_id == Restaurant.id, isouter=True
    ).group_by(Restaurant.id).all()

    ranked = sorted(
        restaurants,
        key=lambda x: (x.avg_rating or 0, x.review_count),
        reverse=True
    )

    top_results = ranked[:5]

    return {
        "query": query,
        "recommendations": [
            {
                "id": r.id,
                "name": r.name,
                "cuisine": r.cuisine_type,
                "average_rating": float(r.avg_rating) if r.avg_rating else 0,
                "review_count": r.review_count
            }
            for r in top_results
        ]
    }