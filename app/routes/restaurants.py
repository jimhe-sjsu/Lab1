from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.favorite import Favorite
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.models.user import User, UserRole
from app.schemas.dashboard import OwnerDashboardResponse, RecentReviewItem, SentimentSummary
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantDetailsResponse,
    RestaurantResponse,
    RestaurantUpdate,
)
from app.schemas.review import ReviewResponse

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


def _with_metrics(restaurant: Restaurant, avg_rating: float | None, review_count: int | None) -> dict:
    payload = {
        column.name: getattr(restaurant, column.name)
        for column in Restaurant.__table__.columns
    }
    payload["average_rating"] = float(avg_rating) if avg_rating is not None else 0
    payload["review_count"] = int(review_count or 0)
    payload["view_count"] = int(getattr(restaurant, "view_count", 0) or 0)
    return payload


def _serialize_review(review: Review, reviewer_name: Optional[str] = None) -> ReviewResponse:
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


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.lower().replace(",", " ").split())


def _owner_location_matches_restaurant(owner_location: str | None, restaurant: Restaurant) -> bool:
    owner_location_normalized = _normalize_text(owner_location)
    if not owner_location_normalized:
        return False

    restaurant_parts = [
        restaurant.address,
        restaurant.city,
        restaurant.state,
        restaurant.zip_code,
        f"{restaurant.city} {restaurant.state}",
        f"{restaurant.address} {restaurant.city} {restaurant.state} {restaurant.zip_code}",
    ]

    normalized_parts = [_normalize_text(part) for part in restaurant_parts if part]
    return any(
        part and (part in owner_location_normalized or owner_location_normalized in part)
        for part in normalized_parts
    )


@router.post("/", response_model=RestaurantResponse)
def create_restaurant(
    restaurant: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_restaurant = Restaurant(
        name=restaurant.name,
        cuisine_type=restaurant.cuisine_type,
        address=restaurant.address,
        city=restaurant.city,
        state=restaurant.state,
        zip_code=restaurant.zip_code,
        description=restaurant.description,
        price_tier=restaurant.price_tier,
        contact_phone=restaurant.contact_phone,
        hours_text=restaurant.hours_text,
        photo_url=restaurant.photo_url,
        amenities_text=restaurant.amenities_text,
        owner_id=current_user.id if current_user.role == UserRole.OWNER else None,
        created_by=current_user.id,
    )

    db.add(new_restaurant)
    db.commit()
    db.refresh(new_restaurant)

    return _with_metrics(new_restaurant, 0, 0)


@router.get("/", response_model=List[RestaurantResponse])
def get_all_restaurants(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Restaurant,
            func.avg(Review.rating).label("average_rating"),
            func.count(Review.id).label("review_count"),
        )
        .outerjoin(Review, Review.restaurant_id == Restaurant.id)
        .group_by(Restaurant.id)
        .order_by(Restaurant.created_at.desc())
        .all()
    )
    return [_with_metrics(restaurant, average_rating, review_count) for restaurant, average_rating, review_count in rows]


@router.get("/search", response_model=List[RestaurantResponse])
def search_restaurants(
    db: Session = Depends(get_db),
    name: Optional[str] = Query(default=None),
    cuisine: Optional[str] = Query(default=None),
    city: Optional[str] = Query(default=None),
    zip_code: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    price_tier: Optional[str] = Query(default=None),
):
    query = (
        db.query(
            Restaurant,
            func.avg(Review.rating).label("average_rating"),
            func.count(Review.id).label("review_count"),
        )
        .outerjoin(Review, Review.restaurant_id == Restaurant.id)
    )

    if name:
        query = query.filter(Restaurant.name.ilike(f"%{name}%"))
    if cuisine:
        query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
    if city:
        query = query.filter(Restaurant.city.ilike(f"%{city}%"))
    if zip_code:
        query = query.filter(Restaurant.zip_code.ilike(f"%{zip_code}%"))
    if price_tier:
        query = query.filter(Restaurant.price_tier == price_tier)

    if keyword:
        query = query.filter(
            or_(
                Restaurant.description.ilike(f"%{keyword}%"),
                Restaurant.amenities_text.ilike(f"%{keyword}%"),
                Restaurant.hours_text.ilike(f"%{keyword}%"),
                Restaurant.name.ilike(f"%{keyword}%"),
                Restaurant.city.ilike(f"%{keyword}%"),
                Restaurant.address.ilike(f"%{keyword}%"),
            )
        )

    rows = query.group_by(Restaurant.id).order_by(Restaurant.created_at.desc()).all()
    return [_with_metrics(restaurant, average_rating, review_count) for restaurant, average_rating, review_count in rows]


@router.get("/{restaurant_id}", response_model=RestaurantDetailsResponse)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    restaurant.view_count = int(restaurant.view_count or 0) + 1
    db.commit()
    db.refresh(restaurant)

    average_rating = db.query(func.avg(Review.rating)).filter(Review.restaurant_id == restaurant_id).scalar()
    review_count = db.query(func.count(Review.id)).filter(Review.restaurant_id == restaurant_id).scalar()

    review_rows = (
        db.query(Review, User.name)
        .join(User, User.id == Review.user_id)
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    reviews = [_serialize_review(review, reviewer_name) for review, reviewer_name in review_rows]

    return RestaurantDetailsResponse(
        restaurant=RestaurantResponse(**_with_metrics(restaurant, average_rating, review_count)),
        average_rating=float(average_rating) if average_rating is not None else 0,
        review_count=int(review_count or 0),
        reviews=reviews,
    )


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(
    restaurant_id: int,
    updates: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    if restaurant.created_by != current_user.id and restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(restaurant, field, value)

    db.commit()
    db.refresh(restaurant)

    average_rating = db.query(func.avg(Review.rating)).filter(Review.restaurant_id == restaurant_id).scalar()
    review_count = db.query(func.count(Review.id)).filter(Review.restaurant_id == restaurant_id).scalar()
    return _with_metrics(restaurant, average_rating, review_count)


@router.delete("/{restaurant_id}")
def delete_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    if restaurant.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(restaurant)
    db.commit()
    return {"message": "Restaurant deleted successfully"}


@router.post("/{restaurant_id}/claim")
def claim_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    if current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owners can claim restaurants")

    if restaurant.owner_id == current_user.id:
        return {"message": "You already manage this restaurant"}
    if restaurant.owner_id and restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="This restaurant has already been claimed")
    if not current_user.restaurant_location:
        raise HTTPException(
            status_code=400,
            detail="Please update your owner profile with a restaurant location before claiming a listing",
        )
    if not _owner_location_matches_restaurant(current_user.restaurant_location, restaurant):
        raise HTTPException(
            status_code=400,
            detail="Owner restaurant location does not match this listing. Update your owner profile first.",
        )

    restaurant.owner_id = current_user.id
    db.commit()
    db.refresh(restaurant)
    return {"message": "Restaurant claimed successfully"}


@router.get("/{restaurant_id}/dashboard", response_model=OwnerDashboardResponse)
def owner_dashboard(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    total_reviews = int(
        db.query(func.count(Review.id)).filter(Review.restaurant_id == restaurant_id).scalar() or 0
    )
    avg_rating = db.query(func.avg(Review.rating)).filter(Review.restaurant_id == restaurant_id).scalar()
    favorite_count = int(
        db.query(func.count(Favorite.id)).filter(Favorite.restaurant_id == restaurant_id).scalar() or 0
    )

    distribution_rows = (
        db.query(Review.rating, func.count(Review.id))
        .filter(Review.restaurant_id == restaurant_id)
        .group_by(Review.rating)
        .all()
    )
    rating_distribution: Dict[str, int] = {str(star): 0 for star in range(1, 6)}
    for rating, count in distribution_rows:
        rating_distribution[str(rating)] = int(count)

    recent_review_rows = (
        db.query(Review, User.name)
        .join(User, User.id == Review.user_id)
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .limit(5)
        .all()
    )
    recent_reviews = [
        RecentReviewItem(
            id=review.id,
            reviewer_name=reviewer_name,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
        )
        for review, reviewer_name in recent_review_rows
    ]

    sentiment = SentimentSummary(
        positive=sum(int(count) for rating, count in distribution_rows if int(rating) >= 4),
        neutral=sum(int(count) for rating, count in distribution_rows if int(rating) == 3),
        negative=sum(int(count) for rating, count in distribution_rows if int(rating) <= 2),
    )

    return OwnerDashboardResponse(
        restaurant=restaurant.name,
        total_reviews=total_reviews,
        average_rating=float(avg_rating) if avg_rating is not None else 0,
        favorite_count=favorite_count,
        total_views=int(restaurant.view_count or 0),
        rating_distribution=rating_distribution,
        recent_reviews=recent_reviews,
        sentiment_summary=sentiment,
    )
