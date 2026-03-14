from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.favorite import Favorite
from app.models.restaurant import Restaurant
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.post("/{restaurant_id}")
def add_favorite(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.restaurant_id == restaurant_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already in favorites")

    favorite = Favorite(
        user_id=current_user.id,
        restaurant_id=restaurant_id
    )

    db.add(favorite)
    db.commit()

    return {"message": "Added to favorites"}
@router.get("/")
def get_my_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Favorite).filter(
        Favorite.user_id == current_user.id
    ).all()
@router.delete("/{restaurant_id}")
def remove_favorite(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.restaurant_id == restaurant_id
    ).first()

    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    db.delete(favorite)
    db.commit()

    return {"message": "Removed from favorites"}