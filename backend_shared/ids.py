from __future__ import annotations

from pymongo import ReturnDocument


def get_next_id(db, counter_name: str) -> int:
    document = db.counters.find_one_and_update(
        {"name": counter_name},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(document["value"])


def set_counter_value(db, counter_name: str, value: int):
    db.counters.update_one(
        {"name": counter_name},
        {"$set": {"value": int(value)}},
        upsert=True,
    )
