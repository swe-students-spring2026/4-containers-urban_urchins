import pytest
import app as ml_app
from pathlib import Path


@pytest.fixture
def client():
    ml_app.app.config["TESTING"] = True
    with ml_app.app.test_client() as client:
        yield client


def test_analyze_return_400_when_image_is_missing(client):
    response = client.post("/analyze", data={})

    assert response.status_code == 400
    assert response.get_json()["error"] == "no image file sent"


def test_analyze_sad_emotion(client):
    image_path = Path(__file__).parent / "images" / "sad.jpg"
    with image_path.open("rb") as image_file:
        response = client.post(
            "/analyze", data={"image": (image_file, image_path.name)}
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"
    assert payload["result"]["dominant_emotion"] == "sad"
