"""flask api for emotion analyze ml client"""

from tempfile import NamedTemporaryFile
from flask import Flask, request, jsonify
from deepface import DeepFace

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

        result = DeepFace.analyze(
            img_path=temp_file.name,
            actions=["emotion"],
            enforce_detection=False,
        )

    if isinstance(result, list):
        result = result[0]

    return {
        "dominant_emotion": result["dominant_emotion"],  # type: ignore
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
