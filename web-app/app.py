import os

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for
import requests

import db as database

load_dotenv()


def create_app(test_config: dict | None = None) -> Flask:
    """Application factory"""
    flask_app = Flask(__name__)
    flask_app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    flask_app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    if test_config:
        flask_app.config.update(test_config)

    @flask_app.route("/")
    def index():
        """Dashboard"""
        results = database.get_recent_results(limit=20)
        return render_template("index.html", results=results)

    @flask_app.route("/upload", methods=["GET"])
    def upload_page():
        """Render upload / capture page"""
        return render_template("upload.html")

    @flask_app.route("/upload", methods=["POST"])
    def upload():
        """Accept upload, persist it to MongoDB, and redirect to dashboard."""
        if "image" not in request.files:
            return redirect(url_for("upload_page"))

        file = request.files["image"]
        if file.filename == "":
            return redirect(url_for("upload_page"))

        image_bytes = file.read()
        if not image_bytes:
            return redirect(url_for("upload_page"))

        inserted_id = database.insert_image(image_bytes, file.filename or "capture.jpg")

        ml_client_url = os.environ.get("ML_CLIENT_URL")
        if ml_client_url:
            try:
                response = requests.post(
                    f"{ml_client_url.rstrip('/')}/analyze",
                    files={"image": (file.filename or "capture.jpg", image_bytes)},
                    timeout=30,
                )
                payload = response.json()
                if response.ok and payload.get("status") == "success":
                    database.save_analysis_results(inserted_id, payload.get("result") or {})
            except requests.RequestException:
                pass
        return redirect(url_for("index"))

    @flask_app.route("/results")
    def results_api():
        """api to return most recent processed analysis results."""
        limit = request.args.get("limit", 50, type=int)
        docs = database.get_all_results_for_api(limit=limit)
        return jsonify(docs)

    @flask_app.route("/results/<image_id>")
    def result_detail(image_id: str):
        """Detail view."""
        result = database.get_image_by_id(image_id)
        if result is None:
            return render_template("404.html"), 404
        return render_template("detail.html", result=result)

    return flask_app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port)
