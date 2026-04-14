import os
from datetime import datetime, timezone

from bson import Binary, ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database


def get_db() -> Database:
    """Return pymongo db instance using env config"""
    mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.environ.get("MONGO_DBNAME", "emotion_detector")
    client = MongoClient(mongo_uri)
    return client[db_name]


def get_images_collection() -> Collection:
    """Return `images`"""
    return get_db()["images"]


def insert_image(image_bytes: bytes, filename: str) -> ObjectId:
    """Store raw image as unprocessed and return ObjectId."""
    collection = get_images_collection()
    doc = {
        "image_data": Binary(image_bytes),
        "filename": filename,
        "uploaded_at": datetime.now(timezone.utc),
        "processed": False,
        "results": None,
    }
    result = collection.insert_one(doc)
    return result.inserted_id


def save_analysis_results(image_id: ObjectId, results: dict) -> None:
    """Mark image as processed w ML results"""
    collection = get_images_collection()
    collection.update_one(
        {"_id": image_id},
        {
            "$set": {
                "processed": True,
                "results": results,
            }
        },
    )


def get_recent_results(limit: int = 20) -> list:
    """Return most recent processed image documents"""
    collection = get_images_collection()
    cursor = (
        collection.find(
            {"processed": True},
            {"image_data": 0},
        )
        .sort("results.processed_at", -1)
        .limit(limit)
    )
    docs = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        docs.append(doc)
    return docs


def get_image_by_id(image_id: str) -> dict | None:
    """Return single image document w id"""
    collection = get_images_collection()
    try:
        oid = ObjectId(image_id)
    except (ValueError, TypeError):
        return None
    doc = collection.find_one({"_id": oid}, {"image_data": 0})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


def get_all_results_for_api(limit: int = 50) -> list:
    """Return as plain dicts for JSON serialization."""
    collection = get_images_collection()
    cursor = (
        collection.find(
            {"processed": True},
            {"image_data": 0},
        )
        .sort("results.processed_at", -1)
        .limit(limit)
    )
    docs = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        if doc.get("uploaded_at"):
            doc["uploaded_at"] = doc["uploaded_at"].isoformat()
        if doc.get("results") and doc["results"].get("processed_at"):
            doc["results"]["processed_at"] = doc["results"][
                "processed_at"
            ].isoformat()
        docs.append(doc)
    return docs
