from __future__ import annotations

import json
from functools import lru_cache

from kafka import KafkaConsumer, KafkaProducer

from backend_shared.config import get_settings
from backend_shared.utils import json_default


@lru_cache(maxsize=1)
def get_kafka_producer() -> KafkaProducer:
    settings = get_settings()
    return KafkaProducer(
        bootstrap_servers=[server.strip() for server in settings.kafka_bootstrap_servers.split(",") if server.strip()],
        value_serializer=lambda payload: json.dumps(payload, default=json_default).encode("utf-8"),
    )


def publish_message(topic: str, payload: dict):
    producer = get_kafka_producer()
    producer.send(topic, payload)
    producer.flush()


def create_consumer(*topics: str, group_id: str):
    settings = get_settings()
    return KafkaConsumer(
        *topics,
        bootstrap_servers=[server.strip() for server in settings.kafka_bootstrap_servers.split(",") if server.strip()],
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )
