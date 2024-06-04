"""Tests for the main module."""

from fastapi.testclient import TestClient

from cid.main import app

# Create a TestClient instance to test the FastAPI app
# https://fastapi.tiangolo.com/tutorial/testing/
client = TestClient(app)


def test_read_root():
    """Test the read_root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}
