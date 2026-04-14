"""Unit tests for the ML client API"""

import io
from unittest.mock import patch
import pytest
from app import app


@pytest.fixture(name="test_client")
def fixture_test_client():
    """Provides a Flask test client for the suite."""
    app.config["TESTING"] = True
    with app.test_client() as client_instance:
        yield client_instance


def test_health_endpoint(test_client):
    """Verify the health check returns 200 and correct message."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json == {"message": "ml client is running"}


def test_analyze_no_image(test_client):
    """Verify 400 error when the 'image' key is missing from the request."""
    response = test_client.post("/analyze")
    assert response.status_code == 400
    assert response.json["error"] == "no image file sent"


def test_analyze_empty_filename(test_client):
    """Verify 400 error when a file is sent with an empty filename."""
    data = {"image": (io.BytesIO(b"content"), "")}
    response = test_client.post(
        "/analyze", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 400
    assert response.json["error"] == "empty filename"


@patch("app.DeepFace.analyze")
def test_analyze_success(mock_deepface, test_client):
    """Test successful analysis by mocking the DeepFace model output."""
    mock_deepface.return_value = [{"dominant_emotion": "happy"}]

    data = {"image": (io.BytesIO(b"fake-image-bytes"), "face.jpg")}
    response = test_client.post(
        "/analyze", data=data, content_type="multipart/form-data"
    )

    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert response.json["result"]["dominant_emotion"] == "happy"
    mock_deepface.assert_called_once()


@patch("app.DeepFace.analyze")
def test_analyze_exception_handling(mock_deepface, test_client):
    """Verify 500 error handling if DeepFace fails internally."""
    mock_deepface.side_effect = Exception("Model failure")

    data = {"image": (io.BytesIO(b"fake-image-bytes"), "face.jpg")}
    response = test_client.post(
        "/analyze", data=data, content_type="multipart/form-data"
    )

    assert response.status_code == 500
    assert response.json["status"] == "error"
    assert "failed to analyze image" in response.json["error"]
