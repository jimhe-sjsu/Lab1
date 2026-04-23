from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    service_name: str
    mongodb_url: str
    mongodb_database: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    uploads_dir: str
    kafka_bootstrap_servers: str
    kafka_review_created_topic: str
    kafka_review_updated_topic: str
    kafka_review_deleted_topic: str
    kafka_review_status_topic: str
    review_status_consumer_enabled: bool
    cors_origins: tuple[str, ...]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    cors_origins = tuple(
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080",
        ).split(",")
        if origin.strip()
    )

    return Settings(
        service_name=os.getenv("SERVICE_NAME", "lab2-service"),
        mongodb_url=os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
        mongodb_database=os.getenv("MONGODB_DATABASE", "lab2_yelp"),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY", "change-me-in-env"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM") or os.getenv("ALGORITHM", "HS256"),
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
        uploads_dir=os.getenv("UPLOADS_DIR", "uploads"),
        kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        kafka_review_created_topic=os.getenv("KAFKA_TOPIC_REVIEW_CREATED", "review.created"),
        kafka_review_updated_topic=os.getenv("KAFKA_TOPIC_REVIEW_UPDATED", "review.updated"),
        kafka_review_deleted_topic=os.getenv("KAFKA_TOPIC_REVIEW_DELETED", "review.deleted"),
        kafka_review_status_topic=os.getenv("KAFKA_TOPIC_REVIEW_STATUS", "booking.status"),
        review_status_consumer_enabled=_parse_bool(os.getenv("REVIEW_STATUS_CONSUMER_ENABLED"), True),
        cors_origins=cors_origins,
    )
