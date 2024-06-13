"""Tests for the main module."""

from unittest.mock import patch

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


@patch("cid.crud.latest_aws_image")
@patch("cid.crud.latest_azure_image")
@patch("cid.crud.latest_google_image")
def test_latest_image(mock_google, mock_azure, mock_aws):
    mock_aws.return_value = {
        "name": "test_image",
        "version": "1.0",
        "date": "2022-01-01",
        "amis": {"us-west-1": "ami-12345678"},
    }
    mock_azure.return_value = {
        "sku": "sku-a",
        "offer": "offer-a",
        "version": "2.0",
        "urn": "urn-b",
    }
    mock_google.return_value = {
        "name": "test_image",
        "version": "1.0",
        "date": "2022-01-01",
        "selfLink": "https://www.example.com",
    }

    response = client.get("/latest")
    result = response.json()

    assert result.keys() == {
        "latest_aws_image",
        "latest_azure_image",
        "latest_google_image",
    }
    assert result["latest_aws_image"]["name"] == "test_image"
    assert result["latest_azure_image"]["sku"] == "sku-a"
    assert result["latest_google_image"]["name"] == "test_image"


@patch("cid.crud.find_available_versions")
def test_versions(mock_versions):
    mock_versions.return_value = ["8.9.0", "9.2.0", "10.0.0"]

    response = client.get("/versions")
    assert response.status_code == 200
    assert response.json() == ["8.9.0", "9.2.0", "10.0.0"]
