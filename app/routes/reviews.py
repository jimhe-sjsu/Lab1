from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["Reviews"])



def _serialize_review(review: Review) -> ReviewResponse:
    reviewer_name = review.user.name if getattr(review, "user", None) else None
    return ReviewResponse(
        id=review.id,
        restaurant_id=review.restaurant_id,
        rating=review.rating,
        comment=review.comment,
        photo_url=review.photo_url,
        user_id=review.user_id,
        reviewer_name=reviewer_name,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.post("/", response_model=ReviewResponse)
def create_review(
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == review.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    new_review = Review(
        restaurant_id=review.restaurant_id,
        rating=review.rating,
        comment=review.comment,
        photo_url=review.photo_url,
        user_id=current_user.id,
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return _serialize_review(new_review)


@router.get("/restaurant/{restaurant_id}", response_model=List[ReviewResponse])
def get_reviews_for_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    reviews = (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    return [_serialize_review(review) for review in reviews]


@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    updates: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = db.query(Review).filter(Review.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update")

    update_data = updates.model_dump(exclude_unset=True)
    if "rating" in update_data:
        review.rating = update_data["rating"]
    if "comment" in update_data:
        review.comment = update_data["comment"]
    if "photo_url" in update_data:
        review.photo_url = update_data["photo_url"]

    db.commit()
    db.refresh(review)

    return _serialize_review(review)


@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = db.query(Review).filter(Review.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete")

    db.delete(review)
    db.commit()

    return {"message": "Review deleted successfully"}
