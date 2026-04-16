"""flask api for emotion analyze ml client"""

import os
from tempfile import NamedTemporaryFile

from deepface import DeepFace
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    """returns a health check response"""
    return jsonify({"message": "ml client is running"}), 200


@app.route("/analyze", methods=["POST"])
def analyze():
    """takes an imgage and returns emotion analysis"""
    if "image" not in request.files:
        return jsonify({"error": "no image file sent"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "empty filename"}), 400

    try:
        analysis = analyze_emotion(file)
        return (
            jsonify(
                {
                    "status": "success",
                    "result": analysis,
                }
            ),
            200,
        )
    except ValueError as exc:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(exc),
                }
            ),
            422,
        )
    except Exception:  # pylint: disable=broad-exception-caught
        return (
            jsonify(
                {
                    "status": "error",
                    "error": "failed to analyze image",
                }
            ),
            500,
        )


def analyze_emotion(uploaded_file):
    """helper funciton that runs DeepFace"""
    with NamedTemporaryFile(suffix=".jpg") as temp_file:
        uploaded_file.save(temp_file.name)

        try:
            result = DeepFace.analyze(
                img_path=temp_file.name,
                actions=["emotion"],
                detector_backend="retinaface",
                align=True,
                enforce_detection=True,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise ValueError("no face detected in image") from exc

    if isinstance(result, list):
        result = result[0]

    emotion_scores = {
        emotion: float(score) for emotion, score in result["emotion"].items() # type: ignore
    }

    return {
        "dominant_emotion": str(result["dominant_emotion"]),  # type: ignore
        "emotion_scores": emotion_scores,
    }


if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
