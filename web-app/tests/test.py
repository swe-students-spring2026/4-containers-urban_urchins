"Unit tests for the Flask web application"

import io
import pytest
from unittest.mock import patch, MagicMock
from app import app as flask_app

@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    return flask_app

@pytest.fixture
def mock_db():
    """Helper to mock the MongoDB connection."""
    with patch('app.get_db') as mocked_get_db:
        mock_database = MagicMock()
        mocked_get_db.return_value = mock_database
        yield mock_database

def test_index_page(client, mock_db):
    """Test successful rendering of the index page with mocked DB."""
    mock_db.images.find.return_value.sort.return_value.limit.return_value = []
    
    response = client.get('/')
    assert response.status_code == 200

def test_upload_no_image(client):
    """Test 400 error for missing image."""
    response = client.post('/upload', data={})
    assert response.status_code == 400
    assert b"no image file provided" in response.data

@patch('app.requests.post')
def test_upload_success(mock_post, client, mock_db):
    """Test successful flow: Image -> ML Client -> MongoDB."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"dominant_emotion": "neutral"}}
    mock_post.return_value = mock_response

    data = {'image': (io.BytesIO(b"fake-bytes"), 'face.jpg')}
    
    response = client.post('/upload', data=data, content_type='multipart/form-data')

    assert response.status_code == 302
    mock_db.images.insert_one.assert_called_once()