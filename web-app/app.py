"""Flask web app"""

import base64
import os
from datetime import datetime, timezone

import requests
from bson import ObjectId
from bson.binary import Binary
from bson.errors import InvalidId
from flask import Flask, jsonify, redirect, render_template, request, url_for
from pymongo import DESCENDING

from db import get_db

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

ML_CLIENT_URL = os.environ.get("ML_CLIENT_URL", "http://ml-client:5000")
RESULTS_LIMIT = 20


@app.route("/")
def index():
    """Dashboard"""
    database = get_db()
    recent = list(
        database.images.find({}, {"image_data": 0})
        .sort("uploaded_at", DESCENDING)
        .limit(RESULTS_LIMIT)
    )
    for item in recent:
        item["_id"] = str(item["_id"])
        if "uploaded_at" in item:
            item["uploaded_at"] = item["uploaded_at"].strftime("%Y-%m-%d %H:%M UTC")
    return render_template("index.html", results=recent)


@app.route("/upload", methods=["GET"])
def upload_page():
    """Render the image page."""
    return render_template("upload.html")


@app.route("/upload", methods=["POST"])
def upload():
    """Accept image, call ML client, and store result"""
    if "image" not in request.files:
        return jsonify({"error": "no image file provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "empty filename"}), 400

    image_data = file.read()
    dominant_emotion = _call_ml_client(image_data, file.filename, file.content_type)

    database = get_db()
    database.images.insert_one(
        {
            "image_data": Binary(image_data),
            "filename": file.filename,
            "uploaded_at": datetime.now(timezone.utc),
            "dominant_emotion": dominant_emotion,
        }
    )
    return redirect(url_for("index"))


@app.route("/results", methods=["GET"])
def results():
    """json api returns analysis results"""
    database = get_db()
    recent = list(
        database.images.find({}, {"image_data": 0})
        .sort("uploaded_at", DESCENDING)
        .limit(RESULTS_LIMIT)
    )
    for item in recent:
        item["_id"] = str(item["_id"])
        if "uploaded_at" in item:
            item["uploaded_at"] = item["uploaded_at"].isoformat()
    return jsonify(recent)


@app.route("/results/<result_id>", methods=["GET"])
def result_detail(result_id):
    """Detail view"""
    try:
        oid = ObjectId(result_id)
    except InvalidId:
        return render_template("404.html"), 404

    database = get_db()
    doc = database.images.find_one({"_id": oid})
    if doc is None:
        return render_template("404.html"), 404

    doc["_id"] = str(doc["_id"])
    if doc.get("image_data"):
        doc["image_b64"] = base64.b64encode(bytes(doc["image_data"])).decode("utf-8")
        del doc["image_data"]
    if "uploaded_at" in doc:
        doc["uploaded_at"] = doc["uploaded_at"].strftime("%Y-%m-%d %H:%M UTC")
    return render_template("detail.html", result=doc)


def _call_ml_client(image_data, filename, content_type):
    """Send image bytes to ML client and return dominant emotion string"""
    try:
        response = requests.post(
            f"{ML_CLIENT_URL}/analyze",
            files={"image": (filename, image_data, content_type or "image/jpeg")},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("result", {}).get("dominant_emotion", "unknown")
    except requests.exceptions.RequestException:
        return "error"


if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
