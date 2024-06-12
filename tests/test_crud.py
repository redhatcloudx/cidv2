"""Tests for CRUD operations."""

from datetime import datetime

from cid import crud
from cid.models import AwsImage, AzureImage, GoogleImage


def test_latest_aws_image_no_images(db):
    result = crud.latest_aws_image(db)
    print(result)
    assert result == {"error": "No images found", "code": 404}


def test_latest_aws_image(db):
    # Two images, same region, different versions.
    images = [
        AwsImage(
            id="ami-a",
            name="test_image_1",
            version="1.0",
            date=datetime.strptime("2022-01-01", "%Y-%m-%d").date(),
            region="us-west-1",
            imageId="ami-a",
        ),
        AwsImage(
            id="ami-b",
            name="test_image_2",
            version="2.0",
            date=datetime.strptime("2022-01-01", "%Y-%m-%d").date(),
            region="us-west-1",
            imageId="ami-b",
        ),
    ]

    db.add_all(images)
    db.commit()

    result = crud.latest_aws_image(db)
    print(result)
    assert result["name"] == "test_image_2"
    assert result["amis"] == {"us-west-1": "ami-b"}

    # Add the same version to another region.
    db.add(
        AwsImage(
            id="ami-c",
            name="test_image_2",
            version="2.0",
            date=datetime.strptime("2022-01-01", "%Y-%m-%d").date(),
            region="us-west-2",
            imageId="ami-c",
        )
    )
    db.commit()

    result = crud.latest_aws_image(db)
    assert result["name"] == "test_image_2"
    assert result["amis"] == {"us-west-1": "ami-b", "us-west-2": "ami-c"}


def test_latest_azure_image_no_images(db):
    result = crud.latest_azure_image(db)
    assert result == {"error": "No images found", "code": 404}


def test_latest_azure_image(db):
    images = [
        AzureImage(
            id="urn-a",
            sku="sku-a",
            offer="offer-a",
            version="1.0",
            urn="urn-a",
        ),
        AzureImage(
            id="urn-b",
            sku="sku-a",
            offer="offer-a",
            version="2.0",
            urn="urn-b",
        ),
    ]
    db.add_all(images)
    db.commit()

    result = crud.latest_azure_image(db)
    assert result["sku"] == "sku-a"
    assert result["version"] == "2.0"


def test_latest_google_image_no_images(db):
    result = crud.latest_google_image(db)
    assert result == {"error": "No images found", "code": 404}


def test_latest_google_image(db):
    images = [
        GoogleImage(
            id="image-a",
            name="test_image_1",
            version="1.0",
            creationTimestamp=datetime.strptime("2022-01-01", "%Y-%m-%d").date(),
        ),
        GoogleImage(
            id="image-b",
            name="test_image_2",
            version="2.0",
            creationTimestamp=datetime.strptime("2022-01-01", "%Y-%m-%d").date(),
        ),
    ]
    db.add_all(images)
    db.commit()

    result = crud.latest_google_image(db)
    assert result["name"] == "test_image_2"
    assert result["version"] == "2.0"
