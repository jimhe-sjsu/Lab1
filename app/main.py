from fastapi import FastAPI, Depends
from app.database import engine, Base
import app.models

# Create FastAPI instance FIRST
app = FastAPI()

from app.routes import auth
from app.routes import restaurants
from app.routes import reviews
from app.routes import favorites
from app.routes import ai
from app.routes import dashboard
from app.routes import home
from app.core.security import get_current_user

# Create tables
Base.metadata.create_all(bind=engine)

# Include routers AFTER app is created
app.include_router(auth.router)
app.include_router(reviews.router)
app.include_router(favorites.router)
app.include_router(ai.router)
app.include_router(restaurants.router)
app.include_router(dashboard.router)
app.include_router(home.router)


@app.get("/")
def root():
    return {"message": "Database Connected 🚀"}


@app.get("/protected")
def protected_route(current_user=Depends(get_current_user)):
    return {
        "message": "You are authenticated",
        "user_id": current_user.id,
        "role": current_user.role
    }