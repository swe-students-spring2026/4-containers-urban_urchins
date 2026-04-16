"Unit tests for the Flask web application"

import io
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest
from bson import ObjectId

import app as web_app
from app import app as flask_app
import db


@pytest.fixture
def app():
    """Fixture to create a test client for the Flask app."""
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture(name="db_client")
def mock_db():
    """Helper to mock the MongoDB connection."""
    with patch("app.get_db") as mocked_get_db:
        mock_database = MagicMock()
        mocked_get_db.return_value = mock_database
        yield mock_database


def test_index_page(client, db_client):
    """Test successful rendering of the index page with mocked DB."""
    db_client.images.find.return_value.sort.return_value.limit.return_value = []

    response = client.get("/")
    assert response.status_code == 200


def test_upload_no_image(client):
    """Test 400 error for missing image."""
    response = client.post("/upload", data={})
    assert response.status_code == 400
    assert b"no image file provided" in response.data


def test_upload_page_renders(client):
    """Test upload page route renders successfully."""
    response = client.get("/upload")
    assert response.status_code == 200


def test_upload_empty_filename(client):
    """Test 400 error when uploaded file has empty name."""
    data = {"image": (io.BytesIO(b"fake-bytes"), "")}

    response = client.post("/upload", data=data, content_type="multipart/form-data")

    assert response.status_code == 400
    assert b"empty filename" in response.data


@patch("app.requests.post")
def test_upload_success(mock_post, client, db_client):
    """Test successful flow: Image -> ML Client -> MongoDB."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"dominant_emotion": "neutral"}}
    mock_post.return_value = mock_response

    data = {"image": (io.BytesIO(b"fake-bytes"), "face.jpg")}

    response = client.post("/upload", data=data, content_type="multipart/form-data")

    assert response.status_code == 302
    db_client.images.insert_one.assert_called_once()


@pytest.fixture(autouse=True)
def reset_db_state_fixture():
    """Ensure each test starts and ends with a clean DB connection state."""
    db.close_db()
    yield
    db.close_db()


def test_get_db_uses_defaults_and_caches():
    """Verify default settings are used and the database is cached."""
    with patch.dict("db.os.environ", {}, clear=True):
        with patch("db.MongoClient") as mock_client_class:
            mock_client = MagicMock()
            mock_database = MagicMock()
            mock_client.__getitem__.return_value = mock_database
            mock_client_class.return_value = mock_client

            first_db = db.get_db()
            second_db = db.get_db()

    mock_client_class.assert_called_once_with("mongodb://localhost:27017")
    mock_client.__getitem__.assert_called_once_with("emotion_detector")
    assert first_db is mock_database
    assert second_db is mock_database


def test_get_db_uses_environment_values():
    """Verify custom env vars are used for Mongo URI and DB name."""
    with patch.dict(
        "db.os.environ",
        {
            "MONGO_URI": "mongodb://mongo:27017",
            "MONGO_DBNAME": "custom_db",
        },
        clear=True,
    ):
        with patch("db.MongoClient") as mock_client_class:
            mock_client = MagicMock()
            mock_database = MagicMock()
            mock_client.__getitem__.return_value = mock_database
            mock_client_class.return_value = mock_client

            result = db.get_db()

    mock_client_class.assert_called_once_with("mongodb://mongo:27017")
    mock_client.__getitem__.assert_called_once_with("custom_db")
    assert result is mock_database


def test_close_db_closes_client_and_resets_state():
    """Verify close_db closes the client and clears cached state."""
    with patch("db.MongoClient") as mock_client_class:
        first_client = MagicMock()
        second_client = MagicMock()
        first_database = MagicMock()
        second_database = MagicMock()

        first_client.__getitem__.return_value = first_database
        second_client.__getitem__.return_value = second_database
        mock_client_class.side_effect = [first_client, second_client]

        db.get_db()
        db.close_db()
        new_db = db.get_db()

    first_client.close.assert_called_once_with()
    assert new_db is second_database
    assert mock_client_class.call_count == 2


def test_close_db_without_client_is_noop():
    """Verify close_db is safe when no client has been created."""
    db.close_db()


def test_results_endpoint_formats_payload(client, db_client):
    """Test /results converts ids and timestamps in returned JSON."""
    uploaded_at = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    db_client.images.find.return_value.sort.return_value.limit.return_value = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "uploaded_at": uploaded_at,
            "dominant_emotion": "neutral",
        }
    ]

    response = client.get("/results")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload[0]["_id"] == "507f1f77bcf86cd799439011"
    assert payload[0]["uploaded_at"] == uploaded_at.isoformat()
    assert payload[0]["dominant_emotion"] == "neutral"


def test_result_detail_invalid_id_returns_404(client):
    """Test detail endpoint returns 404 for invalid ObjectId."""
    response = client.get("/results/not-a-valid-id")
    assert response.status_code == 404


def test_result_detail_not_found_returns_404(client, db_client):
    """Test detail endpoint returns 404 when DB has no matching document."""
    db_client.images.find_one.return_value = None

    response = client.get("/results/507f1f77bcf86cd799439011")

    assert response.status_code == 404
    db_client.images.find_one.assert_called_once()


def test_result_detail_success_encodes_image_and_formats_date(client, db_client):
    """Test detail endpoint renders existing result and transforms fields."""
    uploaded_at = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    db_client.images.find_one.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "image_data": b"abc",
        "uploaded_at": uploaded_at,
        "dominant_emotion": "happy",
    }

    response = client.get("/results/507f1f77bcf86cd799439011")

    assert response.status_code == 200
    assert b"YWJj" in response.data
    assert b"2025-01-01 12:00 UTC" in response.data


@patch("app.requests.post")
def test_call_ml_client_returns_unknown_when_key_missing(mock_post):
    """Test ML helper returns 'unknown' when response lacks emotion data."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": {}}
    mock_post.return_value = mock_response

    call_ml_client = getattr(web_app, "_call_ml_client")
    result = call_ml_client(b"img", "photo.jpg", None)

    assert result == "unknown"
    mock_response.raise_for_status.assert_called_once_with()


@patch("app.requests.post")
def test_call_ml_client_request_exception_returns_error(mock_post):
    """Test ML helper returns 'error' when HTTP request fails."""
    mock_post.side_effect = web_app.requests.exceptions.RequestException

    call_ml_client = getattr(web_app, "_call_ml_client")
    result = call_ml_client(b"img", "photo.jpg", "image/jpeg")

    assert result == "error"
