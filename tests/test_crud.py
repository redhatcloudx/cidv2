"""Tests for CRUD operations."""

import json
from datetime import datetime

from cid import crud
from cid.models import AwsImage, AzureImage, GoogleImage


def test_latest_aws_image_no_images(db):
    result = crud.latest_aws_image(db)
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


def test_import_aws_images(db):
    with open("tests/data/aws.json") as fileh:
        images = json.load(fileh)

    crud.import_aws_images(db, images)

    # The test data contains the first 10 results from a recent AWS API call.
    # curl https://cloudx-json-bucket.s3.amazonaws.com/raw/aws/aws.json |jq ".[0:10]" > tests/data/aws.json
    assert db.query(AwsImage).count() == 10
    assert db.query(AwsImage).first().name == images[0]["Name"]


def test_import_azure_images(db):
    with open("tests/data/azure.json") as fileh:
        images = json.load(fileh)

    crud.import_azure_images(db, images)

    # The test data contains the first 10 results from a recent AWS API call.
    # curl https://cloudx-json-bucket.s3.amazonaws.com/raw/aws/aws.json |jq ".[0:10]" > tests/data/aws.json
    assert db.query(AzureImage).count() == len(images)
    assert db.query(AzureImage).first().urn == images[0]["urn"]


def test_import_google_images(db):
    with open("tests/data/google.json") as fileh:
        images = json.load(fileh)

    crud.import_google_images(db, images)

    # The test data contains the first 10 results from a recent AWS API call.
    # curl https://cloudx-json-bucket.s3.amazonaws.com/raw/aws/aws.json |jq ".[0:10]" > tests/data/aws.json
    assert db.query(GoogleImage).count() == len(images)
    assert db.query(GoogleImage).first().id == images[0]["id"]


def test_find_matching_ami(db):
    # Simulate the same image across two regions with different AMI IDs.
    images = [
        AwsImage(id="ami-a", imageId="ami-a", name="IMAGE01", region="us-east-1"),
        AwsImage(id="ami-b", imageId="ami-b", name="IMAGE01", region="us-east-2"),
    ]
    db.add_all(images)
    db.commit()

    result = crud.find_matching_ami(db, "ami-a")
    assert result["ami"] == "ami-a"
    assert result["matching_images"] == [
        {"region": "us-east-1", "ami": "ami-a"},
        {"region": "us-east-2", "ami": "ami-b"},
    ]


def test_find_available_versions(db):
    images = [
        AwsImage(id="ami-a", version="8.2.0"),
        AwsImage(id="ami-b", version="7.9.0"),
        AwsImage(id="ami-c", version="9.5.0"),
        AwsImage(id="ami-d", version="10.0.0"),
        AwsImage(id="ami-e", version="9.5.0"),
    ]
    db.add_all(images)
    db.commit()

    result = crud.find_available_versions(db)
    assert result == ["10.0.0", "9.5.0", "8.2.0", "7.9.0"]


def test_find_images_for_version(db):
    images = [
        AwsImage(id="ami-a", name="RHEL-8.2.0", version="8.2.0"),
        AwsImage(id="ami-b", name="RHEL-7.9.0", version="7.9.0"),
        AwsImage(id="ami-c", name="RHEL-9.5.0v1", version="9.5.0"),
        AwsImage(id="ami-d", name="RHEL-10.0.0", version="10.0.0"),
        AwsImage(id="ami-e", name="RHEL-9.5.0v2", version="9.5.0"),
    ]
    db.add_all(images)
    db.commit()

    result = crud.find_images_for_version(db, "9.5.0")
    print(result)
    assert result == [
        {"ami": "ami-c", "name": "RHEL-9.5.0v1"},
        {"ami": "ami-e", "name": "RHEL-9.5.0v2"},
    ]
