#!/usr/bin/env python3
"""Import Yelp Open Dataset business records into Lab1 restaurants.

Expected input: yelp_academic_dataset_business.json (JSON lines).

Example:
  python scripts/seed_yelp_business.py \
    --business-json /path/to/yelp_academic_dataset_business.json \
    --state CA --city "San Francisco" --limit 50 --truncate
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

# Ensure `app` package is importable when script runs from Lab1 root.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import app.models  # noqa: F401  # registers SQLAlchemy models
from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models.restaurant import Restaurant
from app.models.user import User, UserRole

GENERIC_CATEGORIES = {
    "restaurants",
    "food",
    "bars",
    "nightlife",
    "event planning & services",
    "hotels & travel",
    "local flavor",
}

AMENITY_KEYS = [
    "OutdoorSeating",
    "WiFi",
    "GoodForKids",
    "NoiseLevel",
    "RestaurantsTakeOut",
    "RestaurantsDelivery",
    "RestaurantsReservations",
    "WheelchairAccessible",
    "BikeParking",
    "Alcohol",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed restaurants from Yelp business dataset")
    parser.add_argument("--business-json", required=True, help="Path to yelp_academic_dataset_business.json")
    parser.add_argument("--limit", type=int, default=30, help="Maximum number of restaurants to import")
    parser.add_argument("--state", type=str, default=None, help="Only import this US state code (example: CA)")
    parser.add_argument("--city", type=str, default=None, help="Only import this city (example: San Jose)")
    parser.add_argument(
        "--min-review-count",
        type=int,
        default=20,
        help="Skip businesses with fewer Yelp reviews than this value",
    )
    parser.add_argument(
        "--include-closed",
        action="store_true",
        help="Include businesses where is_open=0 (default skips closed businesses)",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Delete previously imported Yelp rows before importing",
    )
    parser.add_argument(
        "--update-existing",
        action="store_true",
        help="If same name+address+zip exists, update row instead of skipping",
    )
    parser.add_argument(
        "--created-by-email",
        type=str,
        default="seed+yelp@local",
        help="User email used as created_by for imported restaurants",
    )
    parser.add_argument(
        "--created-by-name",
        type=str,
        default="Yelp Importer",
        help="Name for created_by user if it does not exist",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and report counts but do not write database changes",
    )
    return parser.parse_args()


def parse_categories(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item and item.strip()]


def choose_cuisine(categories: list[str]) -> str:
    for category in categories:
        lowered = category.lower()
        if lowered not in GENERIC_CATEGORIES:
            return category
    return categories[0] if categories else "Restaurant"


def to_price_tier(attributes: dict | None) -> str | None:
    if not attributes:
        return None
    value = attributes.get("RestaurantsPriceRange2")
    if value is None:
        return None
    try:
        level = int(str(value).strip())
    except ValueError:
        return None
    return "$" * max(1, min(level, 4))


def hours_text(hours: dict | None) -> str | None:
    if not isinstance(hours, dict) or not hours:
        return None
    parts = [f"{day}: {value}" for day, value in hours.items() if value]
    if not parts:
        return None
    return " | ".join(parts)[:255]


def amenities_text(attributes: dict | None) -> str | None:
    if not isinstance(attributes, dict) or not attributes:
        return None
    values: list[str] = []
    for key in AMENITY_KEYS:
        raw = attributes.get(key)
        if raw in (None, "", "None"):
            continue
        values.append(f"{key}={raw}")
    if not values:
        return None
    return "; ".join(values)[:500]


def ensure_import_user(db, email: str, name: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user

    user = User(
        name=name,
        email=email,
        password_hash=hash_password("seed-import-account"),
        role=UserRole.OWNER,
    )
    db.add(user)
    db.flush()
    return user


def existing_index(db) -> dict[tuple[str, str, str, str, str], Restaurant]:
    rows = db.query(Restaurant).all()
    out: dict[tuple[str, str, str, str, str], Restaurant] = {}
    for row in rows:
        key = (
            (row.name or "").strip().lower(),
            (row.address or "").strip().lower(),
            (row.city or "").strip().lower(),
            (row.state or "").strip().upper(),
            (row.zip_code or "").strip(),
        )
        out[key] = row
    return out


def is_restaurant(categories: Iterable[str]) -> bool:
    return any(item.lower() == "restaurants" for item in categories)


def main() -> int:
    args = parse_args()
    business_path = Path(args.business_json).expanduser().resolve()

    if not business_path.exists():
        print(f"ERROR: file not found: {business_path}")
        return 1

    if args.limit <= 0:
        print("ERROR: --limit must be > 0")
        return 1

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    scanned = 0
    imported = 0
    updated = 0
    duplicates = 0
    skipped = 0

    try:
        importer = ensure_import_user(db, args.created_by_email, args.created_by_name)

        if args.truncate:
            deleted = (
                db.query(Restaurant)
                .filter(Restaurant.description.like("[YELP:%"))
                .delete(synchronize_session=False)
            )
            print(f"Removed {deleted} existing Yelp-imported restaurants.")

        index = existing_index(db)

        with business_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                if imported >= args.limit:
                    break

                scanned += 1
                line = raw_line.strip()
                if not line:
                    continue

                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    skipped += 1
                    continue

                categories = parse_categories(row.get("categories"))
                if not is_restaurant(categories):
                    continue

                if not args.include_closed and int(row.get("is_open", 0)) != 1:
                    continue

                review_count = int(row.get("review_count") or 0)
                if review_count < args.min_review_count:
                    continue

                city = (row.get("city") or "").strip()
                state = (row.get("state") or "").strip().upper()
                if args.city and city.lower() != args.city.strip().lower():
                    continue
                if args.state and state != args.state.strip().upper():
                    continue

                name = (row.get("name") or "").strip()
                address = (row.get("address") or "").strip()
                postal_code = (row.get("postal_code") or "").strip()
                phone = (row.get("phone") or "").strip() or None

                if not all([name, address, city, state, postal_code]):
                    skipped += 1
                    continue

                key = (name.lower(), address.lower(), city.lower(), state, postal_code)
                cuisine = choose_cuisine(categories)
                description = f"[YELP:{row.get('business_id', 'unknown')}] Categories: {', '.join(categories[:8])}"
                payload = {
                    "name": name,
                    "cuisine_type": cuisine,
                    "description": description,
                    "address": address,
                    "city": city,
                    "state": state,
                    "zip_code": postal_code,
                    "price_tier": to_price_tier(row.get("attributes")),
                    "contact_phone": phone,
                    "hours_text": hours_text(row.get("hours")),
                    "photo_url": f"https://picsum.photos/seed/yelp-{row.get('business_id', scanned)}/1200/800",
                    "amenities_text": amenities_text(row.get("attributes")),
                }

                existing = index.get(key)
                if existing:
                    if args.update_existing:
                        for field, value in payload.items():
                            setattr(existing, field, value)
                        updated += 1
                    else:
                        duplicates += 1
                    continue

                restaurant = Restaurant(
                    **payload,
                    owner_id=None,
                    created_by=importer.id,
                )
                db.add(restaurant)
                imported += 1

                index[key] = restaurant

        if args.dry_run:
            db.rollback()
            print("Dry run complete. No changes written.")
        else:
            db.commit()

        print("Done")
        print(f"Scanned lines: {scanned}")
        print(f"Imported: {imported}")
        print(f"Updated: {updated}")
        print(f"Duplicates skipped: {duplicates}")
        print(f"Other skipped: {skipped}")
        return 0

    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"ERROR: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
