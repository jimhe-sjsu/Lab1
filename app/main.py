from fastapi import Depends, FastAPI
from sqlalchemy import inspect, text

import app.models
from app.core.security import get_current_user
from app.database import Base, engine
from app.routes import auth, dashboard, favorites, home, restaurants, reviews, users
from app.routes import ai_assistant

app = FastAPI()

Base.metadata.create_all(bind=engine)


# Keep schema backward compatible when existing tables were created before new fields.
def _ensure_columns():
    inspector = inspect(engine)
    additions = {
        "users": {
            "phone_number": "VARCHAR(30)",
            "about_me": "VARCHAR(500)",
            "city": "VARCHAR(100)",
            "state": "VARCHAR(10)",
            "country": "VARCHAR(100)",
            "languages": "VARCHAR(200)",
            "gender": "VARCHAR(30)",
            "profile_image_url": "VARCHAR(500)",
        },
        "restaurants": {
            "contact_phone": "VARCHAR(30)",
            "hours_text": "VARCHAR(255)",
            "photo_url": "VARCHAR(500)",
            "amenities_text": "VARCHAR(500)",
        },
        "reviews": {
            "photo_url": "VARCHAR(500)",
        },
    }

    with engine.begin() as conn:
        for table_name, columns in additions.items():
            if table_name not in inspector.get_table_names():
                continue
            existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
            for column_name, definition in columns.items():
                if column_name not in existing_columns:
                    conn.execute(
                        text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition} NULL")
                    )


_ensure_columns()

app.include_router(auth.router)
app.include_router(reviews.router)
app.include_router(favorites.router)
app.include_router(restaurants.router)
app.include_router(dashboard.router)
app.include_router(home.router)
app.include_router(users.router)
app.include_router(ai_assistant.router)


@app.get("/")
def root():
    return {"message": "Database Connected 🚀"}


@app.get("/protected")
def protected_route(current_user=Depends(get_current_user)):
    return {
        "message": "You are authenticated",
        "user_id": current_user.id,
        "role": current_user.role,
    }
