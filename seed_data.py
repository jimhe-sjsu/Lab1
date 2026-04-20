from app.database import SessionLocal
from app.models.restaurant import Restaurant
from app.models.user import User, UserRole
from app.models.review import Review
from app.models.favorite import Favorite

from faker import Faker
import random
from datetime import datetime

fake = Faker()

FOOD_IMAGES = [
    "https://images.unsplash.com/photo-1555396273-367ea4eb4db5",
    "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe",
    "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38",
    "https://images.unsplash.com/photo-1504674900247-0877df9cc836",
    "https://images.unsplash.com/photo-1528605248644-14dd04022da1",
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4",
    "https://images.unsplash.com/photo-1559339352-11d035aa65de",
    "https://images.unsplash.com/photo-1546069901-ba9599a7e63c",
    "https://images.unsplash.com/photo-1504754524776-8f4f37790ca0",
    "https://images.unsplash.com/photo-1498837167922-ddd27525d352",

    "https://images.unsplash.com/photo-1512058564366-c9e3e046c8c0",
    "https://images.unsplash.com/photo-1543353071-873f17a7a088",
    "https://images.unsplash.com/photo-1506089676908-3592f7389d4d",
    "https://images.unsplash.com/photo-1541544741938-0af808871cc0",
    "https://images.unsplash.com/photo-1529042410759-befb1204b468",
    "https://images.unsplash.com/photo-1482049016688-2d3e1b311543",
    "https://images.unsplash.com/photo-1546069901-d5bfd2cbfb1f",
    "https://images.unsplash.com/photo-1565958011703-44f9829ba187",
    "https://images.unsplash.com/photo-1543332164-6e82f355bad8",
    "https://images.unsplash.com/photo-1505253758473-96b7015fcd40",

    "https://images.unsplash.com/photo-1544025162-d76694265947",
    "https://images.unsplash.com/photo-1559847844-d721426d6edc",
    "https://images.unsplash.com/photo-1508739773434-c26b3d09e071",
    "https://images.unsplash.com/photo-1478145046317-39f10e56b5e9",
    "https://images.unsplash.com/photo-1511690743698-d9d85f2fbf38",
    "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe",
    "https://images.unsplash.com/photo-1551782450-a2132b4ba21d",
    "https://images.unsplash.com/photo-1551782450-17144efb9c50",
    "https://images.unsplash.com/photo-1506086679525-9c3f7a7f3e8e",
    "https://images.unsplash.com/photo-1467003909585-2f8a72700288",

    "https://images.unsplash.com/photo-1504674900247-0877df9cc836",
    "https://images.unsplash.com/photo-1553621042-f6e147245754",
    "https://images.unsplash.com/photo-1505253210343-1a3c9b8b7e52",
    "https://images.unsplash.com/photo-1555939594-58d7cb561ad1",
    "https://images.unsplash.com/photo-1505253758473-96b7015fcd40",
    "https://images.unsplash.com/photo-1529042410759-befb1204b468",
    "https://images.unsplash.com/photo-1506084868230-bb9d95c24759",
    "https://images.unsplash.com/photo-1516685018646-549198525c1b",
    "https://images.unsplash.com/photo-1499028344343-cd173ffc68a9",
    "https://images.unsplash.com/photo-1546069901-5ec6a79120b0",

    "https://images.unsplash.com/photo-1551782450-7a7c4bafc38c",
    "https://images.unsplash.com/photo-1506089676908-3592f7389d4d",
    "https://images.unsplash.com/photo-1544025162-d76694265947",
    "https://images.unsplash.com/photo-1476224203421-9ac39bcb3327",
    "https://images.unsplash.com/photo-1508736793122-f516e3ba5569",
    "https://images.unsplash.com/photo-1550547660-d9450f859349",
    "https://images.unsplash.com/photo-1551782450-17144efb9c50",
    "https://images.unsplash.com/photo-1565299507177-b0ac66763828",
    "https://images.unsplash.com/photo-1504674900247-ec6e0d1ec8f6",
    "https://images.unsplash.com/photo-1506084868230-bb9d95c24759"
]

CUISINES = [
    "Indian", "Italian", "Chinese", "Mexican", "Thai",
    "American", "Mediterranean", "Japanese", "Korean", "Vegan"
]

CITIES = [
    "San Jose", "Santa Clara", "Sunnyvale", "Mountain View", "Cupertino"
]

AMENITIES = [
    "vegan", "family-friendly", "romantic", "takeout", "dine-in",
    "outdoor seating", "pet-friendly", "wifi"
]


def seed():
    db = SessionLocal()

    try:
        # ---- Get users ----
        owner = db.query(User).filter(User.role == UserRole.OWNER).first()
        users = db.query(User).filter(User.role == UserRole.USER).all()

        if not owner or not users:
            print("❌ Need at least 1 OWNER and 1 USER")
            return

        # ---- Clean existing data (optional but useful) ----
        db.query(Favorite).delete()
        db.query(Review).delete()
        db.query(Restaurant).delete()
        db.commit()

        print("🧹 Old data cleared")

        restaurants = []

        # ---- Create many restaurants ----
        for i in range(30):
            cuisine = random.choice(CUISINES)
            city = random.choice(CITIES)

            restaurant = Restaurant(
                name=fake.company() + " " + cuisine,
                cuisine_type=cuisine,
                address=fake.street_address(),
                city=city,
                state="CA",
                zip_code=fake.zipcode(),
                description=f"{cuisine} restaurant serving delicious food",
                price_tier=random.choice(["$", "$$", "$$$"]),
                contact_phone=fake.phone_number(),
                hours_text="Mon-Sun 10AM - 10PM",
                photo_url=random.choice(FOOD_IMAGES),
                amenities_text=", ".join(random.sample(AMENITIES, 3)),
                owner_id=owner.id,
                created_by=owner.id,
            )

            db.add(restaurant)
            restaurants.append(restaurant)

        db.commit()

        for r in restaurants:
            db.refresh(r)

        print("✅ 30 Restaurants added")

        # ---- Create reviews ----
        reviews = []

        for restaurant in restaurants:
            num_reviews = random.randint(2, 6)

            for _ in range(num_reviews):
                user = random.choice(users)

                review = Review(
                    user_id=user.id,
                    restaurant_id=restaurant.id,
                    rating=random.randint(1, 5),
                    comment=fake.sentence(),
                    created_at=datetime.utcnow(),
                )

                reviews.append(review)

        db.add_all(reviews)
        db.commit()

        print("✅ Reviews added")

        # ---- Create favorites ----
        favorites = []

        for user in users:
            fav_restaurants = random.sample(restaurants, k=min(5, len(restaurants)))

            for r in fav_restaurants:
                favorites.append(Favorite(user_id=user.id, restaurant_id=r.id))

        db.add_all(favorites)
        db.commit()

        print("✅ Favorites added")

        print("🎉 Seeding complete!")

    except Exception as e:
        db.rollback()
        print("❌ Error:", e)

    finally:
        db.close()


if __name__ == "__main__":
    seed()