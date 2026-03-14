from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.review import Review
from app.models.favorite import Favorite
from app.core.security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/user")
def user_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_reviews = db.query(func.count(Review.id)).filter(
        Review.user_id == current_user.id
    ).scalar()

    total_favorites = db.query(func.count(Favorite.id)).filter(
        Favorite.user_id == current_user.id
    ).scalar()

    return {
        "user": current_user.email,
        "total_reviews": total_reviews,
        "total_favorites": total_favorites
    }