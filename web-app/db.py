"""MongoDB connection helper for web app."""

import os
from typing import Any

from pymongo import MongoClient

_state: dict[str, Any] = {"client": None, "database": None}


def get_db():
    """Return shared db instance, creating on first call."""
    if _state["database"] is None:
        mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
        db_name = os.environ.get("MONGO_DBNAME", "emotion_detector")
        client = MongoClient(mongo_uri)
        _state["client"] = client
        _state["database"] = client[db_name]
    return _state["database"]


def close_db():
    """Close MongoDB connection. For tests."""
    if _state["client"] is not None:
        _state["client"].close()
        _state["client"] = None
        _state["database"] = None
