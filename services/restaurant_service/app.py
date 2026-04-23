from __future__ import annotations

from fastapi import Depends, HTTPException, Query

from backend_shared.activity import record_activity
from backend_shared.auth import get_current_user
from backend_shared.db import get_database
from backend_shared.ids import get_next_id
from backend_shared.query_helpers import build_restaurant_details, search_restaurant_documents, serialize_restaurant_list
from backend_shared.schemas import RestaurantCreate, RestaurantDetailsResponse, RestaurantResponse, RestaurantUpdate
from backend_shared.serializers import serialize_restaurant
from backend_shared.service_factory import create_service_app
from backend_shared.utils import utcnow

app = create_service_app(
    title="Lab 2 Restaurant Service",
    description="Restaurant CRUD, search, and detail views backed by MongoDB.",
)


@app.post("/restaurants/", response_model=RestaurantResponse)
def create_restaurant(payload: RestaurantCreate, current_user: dict = Depends(get_current_user())):
    db = get_database()
    restaurant_id = get_next_id(db, "restaurants")
    document = {
        "id": restaurant_id,
        "name": payload.name,
        "cuisine_type": payload.cuisine_type,
        "address": payload.address,
        "city": payload.city,
        "state": payload.state,
        "zip_code": payload.zip_code,
        "description": payload.description,
        "price_tier": payload.price_tier,
        "contact_phone": payload.contact_phone,
        "hours_text": payload.hours_text,
        "photo_url": payload.photo_url,
        "amenities_text": payload.amenities_text,
        "view_count": 0,
        "owner_id": current_user["id"] if current_user.get("role") == "OWNER" else None,
        "created_by": current_user["id"],
        "created_at": utcnow(),
    }
    db.restaurants.insert_one(document)
    record_activity(
        db,
        user_id=current_user["id"],
        event_type="restaurant.created",
        restaurant_id=restaurant_id,
        metadata={"restaurant_name": payload.name},
    )
    return RestaurantResponse(**serialize_restaurant(document))


@app.get("/restaurants/", response_model=list[RestaurantResponse])
def get_all_restaurants():
    db = get_database()
    return [RestaurantResponse(**restaurant) for restaurant in serialize_restaurant_list(db, list(db.restaurants.find({}).sort("created_at", -1)))]


@app.get("/restaurants/search", response_model=list[RestaurantResponse])
def search_restaurants(
    name: str | None = Query(default=None),
    cuisine: str | None = Query(default=None),
    city: str | None = Query(default=None),
    zip_code: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    price_tier: str | None = Query(default=None),
):
    db = get_database()
    restaurants = search_restaurant_documents(
        db,
        {
            "name": name,
            "cuisine": cuisine,
            "city": city,
            "zip_code": zip_code,
            "keyword": keyword,
            "price_tier": price_tier,
        },
    )
    return [RestaurantResponse(**restaurant) for restaurant in serialize_restaurant_list(db, restaurants)]


@app.get("/restaurants/{restaurant_id}", response_model=RestaurantDetailsResponse)
def get_restaurant(restaurant_id: int):
    db = get_database()
    restaurant = db.restaurants.find_one({"id": restaurant_id})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    db.restaurants.update_one({"id": restaurant_id}, {"$inc": {"view_count": 1}})
    details = build_restaurant_details(db, restaurant_id)
    return RestaurantDetailsResponse(**details)


@app.put("/restaurants/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(restaurant_id: int, updates: RestaurantUpdate, current_user: dict = Depends(get_current_user())):
    db = get_database()
    restaurant = db.restaurants.find_one({"id": restaurant_id})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if restaurant.get("created_by") != current_user["id"] and restaurant.get("owner_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = {key: value for key, value in updates.model_dump(exclude_unset=True).items()}
    if update_data:
        db.restaurants.update_one({"id": restaurant_id}, {"$set": update_data})

    refreshed = db.restaurants.find_one({"id": restaurant_id})
    details = build_restaurant_details(db, restaurant_id)
    return RestaurantResponse(**details["restaurant"])


@app.delete("/restaurants/{restaurant_id}")
def delete_restaurant(restaurant_id: int, current_user: dict = Depends(get_current_user())):
    db = get_database()
    restaurant = db.restaurants.find_one({"id": restaurant_id})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if restaurant.get("created_by") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.restaurants.delete_one({"id": restaurant_id})
    db.reviews.delete_many({"restaurant_id": restaurant_id})
    db.favorites.delete_many({"restaurant_id": restaurant_id})
    return {"message": "Restaurant deleted successfully"}
