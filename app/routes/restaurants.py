from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.models.favorite import Favorite
from app.models.user import User
from app.core.security import get_current_user

from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantResponse
)

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


# 🔥 CREATE RESTAURANT (JSON BODY)
@router.post("/", response_model=RestaurantResponse)
def create_restaurant(
    restaurant: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
        created_by=current_user.id
    )

    db.add(new_restaurant)
    db.commit()
    db.refresh(new_restaurant)

    return new_restaurant


# 🔥 GET ALL RESTAURANTS (PUBLIC)
@router.get("/", response_model=List[RestaurantResponse])
def get_all_restaurants(db: Session = Depends(get_db)):
    return db.query(Restaurant).all()


# 🔥 GET SINGLE RESTAURANT (YELP STYLE)
@router.get("/{restaurant_id}")
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):

    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    average_rating = db.query(func.avg(Review.rating)).filter(
        Review.restaurant_id == restaurant_id
    ).scalar()

    review_count = db.query(func.count(Review.id)).filter(
        Review.restaurant_id == restaurant_id
    ).scalar()

    reviews = db.query(Review).filter(
        Review.restaurant_id == restaurant_id
    ).all()

    return {
        "restaurant": restaurant,
        "average_rating": float(average_rating) if average_rating else 0,
        "review_count": review_count,
        "reviews": reviews
    }


# 🔥 UPDATE RESTAURANT (JSON BODY)
@router.put("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(
    restaurant_id: int,
    updates: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    if restaurant.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if updates.name is not None:
        restaurant.name = updates.name

    if updates.cuisine_type is not None:
        restaurant.cuisine_type = updates.cuisine_type

    if updates.description is not None:
        restaurant.description = updates.description

    if updates.price_tier is not None:
        restaurant.price_tier = updates.price_tier

    db.commit()
    db.refresh(restaurant)

    return restaurant


# 🔥 DELETE RESTAURANT
@router.delete("/{restaurant_id}")
def delete_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    if restaurant.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(restaurant)
    db.commit()

    return {"message": "Restaurant deleted successfully"}


# 🔥 SEARCH (PUBLIC)
@router.get("/search/")
def search_restaurants(
    city: str = None,
    cuisine: str = None,
    price_tier: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Restaurant)

    if city:
        query = query.filter(Restaurant.city.ilike(f"%{city}%"))

    if cuisine:
        query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))

    if price_tier:
        query = query.filter(Restaurant.price_tier == price_tier)

    return query.all()


# 🔥 CLAIM RESTAURANT
@router.post("/{restaurant_id}/claim")
def claim_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    if restaurant.owner_id:
        raise HTTPException(status_code=400, detail="Already claimed")

    restaurant.owner_id = current_user.id

    db.commit()
    db.refresh(restaurant)

    return {"message": "Restaurant claimed successfully"}


# 🔥 OWNER DASHBOARD
@router.get("/{restaurant_id}/dashboard")
def owner_dashboard(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    if restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    total_reviews = db.query(func.count(Review.id)).filter(
        Review.restaurant_id == restaurant_id
    ).scalar()

    avg_rating = db.query(func.avg(Review.rating)).filter(
        Review.restaurant_id == restaurant_id
    ).scalar()

    favorite_count = db.query(func.count(Favorite.id)).filter(
        Favorite.restaurant_id == restaurant_id
    ).scalar()

    return {
        "restaurant": restaurant.name,
        "total_reviews": total_reviews,
        "average_rating": float(avg_rating) if avg_rating else 0,
        "favorite_count": favorite_count
    }