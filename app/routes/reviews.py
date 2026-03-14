from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.review import Review
from app.models.restaurant import Restaurant
from app.models.user import User
from app.core.security import get_current_user
from app.schemas.review import ReviewCreate, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewResponse)
def create_review(
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check restaurant exists
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == review.restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    new_review = Review(
        restaurant_id=review.restaurant_id,
        rating=review.rating,
        comment=review.comment,
        user_id=current_user.id
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return new_review


@router.get("/restaurant/{restaurant_id}")
def get_reviews_for_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    return db.query(Review).filter(Review.restaurant_id == restaurant_id).all()


@router.put("/{review_id}")
def update_review(
    review_id: int,
    rating: int = None,
    comment: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = db.query(Review).filter(Review.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update")

    if rating:
        review.rating = rating
    if comment:
        review.comment = comment

    db.commit()
    db.refresh(review)

    return review


@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = db.query(Review).filter(Review.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete")

    db.delete(review)
    db.commit()

    return {"message": "Review deleted successfully"}