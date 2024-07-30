"""Tests for the main module."""

import json
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cid import crud
from cid.database import Base
from cid.main import app, check_endpoint_status, get_db

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

    with open("tests/data/azure.json") as fileh:
        images = json.load(fileh)
    crud.import_azure_images(db, images)

    with open("tests/data/google.json") as fileh:
        images = json.load(fileh)
    crud.import_google_images(db, images)


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_check_endpoint_status_running():
    def mock_endpoint_func(db, *args, **kwargs):
        return "data"

    result = check_endpoint_status(None, mock_endpoint_func)
    assert result == "running"


def test_check_endpoint_status_down():
    def mock_endpoint_func(db, *args, **kwargs):
        return None

    result = check_endpoint_status(None, mock_endpoint_func)
    assert result == "down"


def test_check_endpoint_status_exception():
    def mock_endpoint_func(db, *args, **kwargs):
        raise HTTPException(status_code=500)

    result = check_endpoint_status(None, mock_endpoint_func)
    assert result == "down"


def test_read_root():
    """Test the read_root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == {
        "https://testserver/aws": "running",
        "https://testserver/google": "running",
        "https://testserver/azure": "running",
    }
    assert "docs" in response.json()
    assert "last_update" in response.json()


@patch("cid.crud.latest_aws_image")
def test_latest_aws_image(mock_aws):
    mock_aws.return_value = {
        "name": "test_image",
        "version": "1.0",
        "date": "2022-01-01",
        "amis": {"af-south-1": "ami-12345678"},
    }

    response = client.get("/aws/latest")
    result = response.json()

    assert response.status_code == 200
    assert result["name"] == "test_image"
    assert result["version"] == "1.0"
    assert result["date"] == "2022-01-01"
    assert result["amis"] == {"af-south-1": "ami-12345678"}


@patch("cid.crud.latest_aws_image")
def test_latest_aws_image_query_for_arch(mock_aws):
    mock_aws.return_value = {
        "name": "test_image",
        "version": "1.0",
        "date": "2022-01-01",
        "amis": {"af-south-1": "ami-12345678"},
    }

    response = client.get("/aws/latest?arch=x86_64")
    result = response.json()

    assert response.status_code == 200
    assert result["name"] == "test_image"
    assert result["version"] == "1.0"
    assert result["date"] == "2022-01-01"
    assert result["amis"] == {"af-south-1": "ami-12345678"}


@patch("cid.crud.find_available_aws_versions")
def test_aws_versions(mock_versions):
    mock_versions.return_value = ["8.9.0", "9.2.0", "10.0.0"]

    response = client.get("/aws/versions")
    assert response.status_code == 200
    assert response.json() == ["8.9.0", "9.2.0", "10.0.0"]


@patch("cid.crud.find_available_azure_versions")
def test_azure_versions(mock_versions):
    mock_versions.return_value = ["8.9.0", "9.2.0", "10.0.0"]

    response = client.get("/azure/versions")
    assert response.status_code == 200
    assert response.json() == ["8.9.0", "9.2.0", "10.0.0"]


@patch("cid.crud.find_available_google_versions")
def test_google_versions(mock_versions):
    mock_versions.return_value = ["8.9.0", "9.2.0", "10.0.0"]

    response = client.get("/google/versions")
    assert response.status_code == 200
    assert response.json() == ["8.9.0", "9.2.0", "10.0.0"]


def test_all_aws_images():
    response = client.get("/aws")
    assert response.status_code == 200
    assert len(response.json()["results"]) == 100
    assert response.json()["page"] == 1
    assert response.json()["page_size"] == 100
    assert response.json()["total_count"] == 500
    assert response.json()["total_pages"] == 5


def test_all_aws_images_paginated():
    response = client.get("/aws?page=2&page_size=1")
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["page"] == 2
    assert response.json()["page_size"] == 1
    assert response.json()["total_count"] == 500
    assert response.json()["total_pages"] == 500


def test_all_aws_images_with_query():
    response = client.get("/aws?version=9.4.0")
    assert response.status_code == 200
    assert response.json()["results"][0]["version"] == "9.4.0"


def test_all_aws_images_with_query_region():
    response = client.get("/aws?region=af-south-1")
    assert response.status_code == 200
    assert response.json()["results"][0]["region"] == "af-south-1"


def test_all_aws_images_with_query_arch():
    response = client.get("/aws?arch=x86_64")
    assert response.status_code == 200
    assert response.json()["results"][0]["arch"] == "x86_64"


def test_all_aws_images_with_query_name():
    response = client.get("/aws?name=RHEL_HA-9.4.0_HVM-20240605-x86_64-82-Hourly2-GP3")
    assert response.status_code == 200
    assert (
        response.json()["results"][0]["name"]
        == "RHEL_HA-9.4.0_HVM-20240605-x86_64-82-Hourly2-GP3"
    )


def test_all_aws_images_with_query_image_id():
    response = client.get("/aws?image_id=ami-08a20c15f394e5531")
    assert response.status_code == 200
    assert (
        response.json()["results"][0]["name"]
        == "RHEL_HA-9.4.0_HVM-20240605-x86_64-82-Hourly2-GP3"
    )


def test_all_aws_images_with_query_combination():
    response = client.get(
        "/aws"
        + "?name=RHEL_HA-9.4.0_HVM-20240605-x86_64-82-Hourly2-GP3"
        + "&region=af-south-1"
        + "&version=9.4.0"
        + "&arch=x86_64"
        + "&image_id=ami-08a20c15f394e5531"
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert (
        response.json()["results"][0]["name"]
        == "RHEL_HA-9.4.0_HVM-20240605-x86_64-82-Hourly2-GP3"
    )
    assert response.json()["results"][0]["region"] == "af-south-1"
    assert response.json()["results"][0]["version"] == "9.4.0"
    assert response.json()["results"][0]["arch"] == "x86_64"


def test_all_aws_images_with_query_combination_no_match():
    response = client.get(
        "/aws"
        + "?name=THIS_DOES_NOT_EXIST"
        + "&region=af-south-1"
        + "&version=9.4.0"
        + "&arch=arm64"
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) == 0


def test_match_aws_image():
    response = client.get("/aws/match/ami-08a20c15f394e5531")
    assert response.status_code == 200
    assert response.json()["name"] == "RHEL_HA-9.4.0_HVM-20240605-x86_64-82-Hourly2-GP3"
    assert "ami" in response.json()["matching_images"][0]
    assert "region" in response.json()["matching_images"][0]


def test_all_azure_images():
    response = client.get("/azure")
    assert response.status_code == 200
    assert len(response.json()["results"]) == 100
    assert response.json()["page"] == 1
    assert response.json()["page_size"] == 100
    assert response.json()["total_count"] == 152
    assert response.json()["total_pages"] == 2


def test_all_azure_images_with_query():
    response = client.get("/azure?version=7.9.2023062711")
    assert response.status_code == 200
    assert response.json()["results"][0]["version"] == "7.9.2023062711"


def test_all_azure_images_with_query_urn():
    response = client.get("/azure?urn=redhat-rhel:rh-rhel:rh-rhel7:7.9.2023062711")
    assert response.status_code == 200
    assert (
        response.json()["results"][0]["urn"]
        == "redhat-rhel:rh-rhel:rh-rhel7:7.9.2023062711"
    )


def test_all_azure_images_with_query_arch():
    response = client.get("/azure?arch=x64")
    assert response.status_code == 200
    assert response.json()["results"][0]["architecture"] == "x64"


def test_all_azure_images_with_query_combination():
    response = client.get(
        "/azure"
        + "?urn=redhat-rhel:rh-rhel:rh-rhel7:7.9.2023062711"
        + "&version=7.9.2023062711"
        + "&arch=x64"
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert (
        response.json()["results"][0]["urn"]
        == "redhat-rhel:rh-rhel:rh-rhel7:7.9.2023062711"
    )
    assert response.json()["results"][0]["version"] == "7.9.2023062711"
    assert response.json()["results"][0]["architecture"] == "x64"


def test_all_azure_images_with_query_combination_no_match():
    response = client.get(
        "/azure"
        + "?urn=rhel-does-not-exist:11.4:11.4.0"
        + "&version=11.4.0"
        + "&architecture=arm64"
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) == 0


@patch("cid.crud.latest_azure_image")
def test_latest_azure_image(mock_azure):
    mock_azure.return_value = {
        "sku": "sku-a",
        "offer": "offer-a",
        "version": "2.0",
        "urn": "urn-b",
    }

    response = client.get("/azure/latest")
    result = response.json()

    assert result["sku"] == "sku-a"
    assert result["offer"] == "offer-a"
    assert result["version"] == "2.0"
    assert result["urn"] == "urn-b"


def test_all_google_images():
    response = client.get("/google")
    assert response.status_code == 200
    assert len(response.json()["results"]) == 4
    assert response.json()["page"] == 1
    assert response.json()["page_size"] == 100
    assert response.json()["total_count"] == 4
    assert response.json()["total_pages"] == 1


def test_all_google_images_with_query():
    response = client.get("/google?version=7")
    assert response.status_code == 200
    assert response.json()["results"][0]["version"] == "7"


def test_all_google_images_with_query_arch():
    response = client.get("/google?arch=X86_64")
    assert response.status_code == 200
    assert response.json()["results"][0]["arch"] == "X86_64"


def test_all_google_images_with_query_name():
    response = client.get("/google?name=rhel-7-v20240611")
    assert response.status_code == 200
    assert response.json()["results"][0]["name"] == "rhel-7-v20240611"


def test_all_google_images_with_query_combination():
    response = client.get(
        "/google" + "?name=rhel-7-v20240611" + "&version=7" + "&arch=X86_64"
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["name"] == "rhel-7-v20240611"
    assert response.json()["results"][0]["version"] == "7"
    assert response.json()["results"][0]["arch"] == "X86_64"


def test_all_google_images_with_query_combination_no_match():
    response = client.get(
        "/google" + "?name=does-not-exist" + "&version=7" + "&arch=X86_64"
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) == 0


@patch("cid.crud.latest_google_image")
def test_latest_google_image(mock_google):
    mock_google.return_value = {
        "name": "test_image",
        "arch": "X86_64",
        "version": "1.0",
        "date": "2022-01-01",
        "selfLink": "link",
    }

    response = client.get("/google/latest")
    result = response.json()

    assert response.status_code == 200
    assert result["name"] == "test_image"
    assert result["arch"] == "X86_64"
    assert result["version"] == "1.0"
    assert result["date"] == "2022-01-01"
    assert result["selfLink"] == "link"


@patch("cid.crud.latest_google_image")
def test_latest_google_image_query_for_arch(mock_google):
    mock_google.return_value = {
        "name": "test_image",
        "arch": "X86_64",
        "version": "1.0",
        "date": "2022-01-01",
        "selfLink": "link",
    }

    response = client.get("/google/latest?arch=x86_64")
    result = response.json()

    assert response.status_code == 200
    assert result["name"] == "test_image"
    assert result["arch"] == "X86_64"
    assert result["version"] == "1.0"
    assert result["date"] == "2022-01-01"
    assert result["selfLink"] == "link"
