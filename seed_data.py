from app.database import SessionLocal
from app.models.restaurant import Restaurant
from app.models.user import User, UserRole
from app.models.review import Review
from app.models.favorite import Favorite

from faker import Faker
import random
from datetime import datetime

fake = Faker()


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
                photo_url=f"https://source.unsplash.com/400x300/?{cuisine},food",
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


#main commit check.