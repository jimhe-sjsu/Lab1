from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.favorite import Favorite
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.models.user import User, UserRole
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse, RestaurantUpdate

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


def _with_metrics(restaurant: Restaurant, avg_rating: float | None, review_count: int | None):
    payload = {
        column.name: getattr(restaurant, column.name)
        for column in Restaurant.__table__.columns
    }
    payload["average_rating"] = float(avg_rating) if avg_rating else 0
    payload["review_count"] = int(review_count or 0)
    return payload


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
        created_by=current_user.id,
    )

    db.add(new_restaurant)
    db.commit()
    db.refresh(new_restaurant)

    return new_restaurant


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
                Restaurant.name.ilike(f"%{keyword}%"),
            )
        )

    rows = query.group_by(Restaurant.id).order_by(Restaurant.created_at.desc()).all()
    return [_with_metrics(restaurant, average_rating, review_count) for restaurant, average_rating, review_count in rows]


@router.get("/{restaurant_id}")
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    average_rating = db.query(func.avg(Review.rating)).filter(Review.restaurant_id == restaurant_id).scalar()

    review_count = db.query(func.count(Review.id)).filter(Review.restaurant_id == restaurant_id).scalar()

    reviews = db.query(Review).filter(Review.restaurant_id == restaurant_id).order_by(Review.created_at.desc()).all()

    return {
        "restaurant": restaurant,
        "average_rating": float(average_rating) if average_rating else 0,
        "review_count": review_count,
        "reviews": reviews,
    }


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

    return restaurant


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

    if restaurant.owner_id:
        raise HTTPException(status_code=400, detail="Already claimed")

    if current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owners can claim restaurants")

    restaurant.owner_id = current_user.id

    db.commit()
    db.refresh(restaurant)

    return {"message": "Restaurant claimed successfully"}


@router.get("/{restaurant_id}/dashboard")
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

    total_reviews = db.query(func.count(Review.id)).filter(Review.restaurant_id == restaurant_id).scalar()

    avg_rating = db.query(func.avg(Review.rating)).filter(Review.restaurant_id == restaurant_id).scalar()

    favorite_count = db.query(func.count(Favorite.id)).filter(Favorite.restaurant_id == restaurant_id).scalar()

    return {
        "restaurant": restaurant.name,
        "total_reviews": total_reviews,
        "average_rating": float(avg_rating) if avg_rating else 0,
        "favorite_count": favorite_count,
    }
