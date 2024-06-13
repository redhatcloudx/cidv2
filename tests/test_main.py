"""Tests for the main module."""

import json
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cid import crud
from cid.database import Base
from cid.main import app, get_db

engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, echo=False
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        Base.metadata.create_all(bind=engine)
        load_test_data()
        yield db
    finally:
        Base.metadata.drop_all(bind=engine)
        db.close()


def load_test_data():
    db = TestingSessionLocal()
    with open("tests/data/aws.json") as fileh:
        images = json.load(fileh)
    crud.import_aws_images(db, images)


app.dependency_overrides[get_db] = override_get_db

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


def test_all_aws_images():
    response = client.get("/aws")
    assert response.status_code == 200
    assert len(response.json()) == 500


def test_single_aws_image():
    response = client.get("/aws/ami-08a20c15f394e5531")
    assert response.status_code == 200
    assert response.json()["name"] == "RHEL_HA-9.4.0_HVM-20240605-x86_64-82-Hourly2-GP3"


def test_match_aws_image():
    response = client.get("/aws/match/ami-08a20c15f394e5531")
    assert response.status_code == 200
    assert response.json()["name"] == "RHEL_HA-9.4.0_HVM-20240605-x86_64-82-Hourly2-GP3"
    assert "ami" in response.json()["matching_images"][0]
    assert "region" in response.json()["matching_images"][0]
