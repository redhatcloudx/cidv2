"""Tests for CRUD operations."""

import json
from datetime import datetime

from cid import crud
from cid.models import AwsImage, AzureImage, GoogleImage


def test_latest_aws_image_no_images(db):
    result = crud.latest_aws_image(db, None)
    assert result == {"error": "No images found for AWS.", "code": 404}


def test_latest_aws_image(db):
    # Two images, same region, different versions.
    images = [
        AwsImage(
            id="ami-1a",
            name="test_image_1a",
            arch="x86_64",
            version="1.0",
            date=datetime.strptime("2022-01-01", "%Y-%m-%d").date(),
            region="us-west-1",
            imageId="ami-1a",
        ),
        AwsImage(
            id="ami-1b",
            name="test_image_1b",
            arch="x86_64",
            version="2.0",
            date=datetime.strptime("2022-01-01", "%Y-%m-%d").date(),
            region="us-west-1",
            imageId="ami-1b",
        ),
        AwsImage(
            id="ami-2a",
            name="test_image_2a",
            arch="arm64",
            version="1.0",
            date=datetime.strptime("2022-01-01", "%Y-%m-%d").date(),
            region="us-west-1",
            imageId="ami-2a",
        ),
        AwsImage(
            id="ami-2b",
            name="test_image_2b",
            arch="arm64",
            version="2.0",
            date=datetime.strptime("2022-01-01", "%Y-%m-%d").date(),
            region="us-west-1",
            imageId="ami-2b",
        ),
    ]

    db.add_all(images)
    db.commit()

    result = crud.latest_aws_image(db, None)
    assert result["x86_64"]["name"] == "test_image_1b"
    assert result["x86_64"]["amis"] == {"us-west-1": "ami-1b"}
    assert result["arm64"]["name"] == "test_image_2b"
    assert result["arm64"]["amis"] == {"us-west-1": "ami-2b"}

    # Add the same version to another region.
    db.add(
        AwsImage(
            id="ami-c",
            name="test_image_2b",
            version="2.0",
            arch="arm64",
            date=datetime.strptime("2022-01-01", "%Y-%m-%d").date(),
            region="us-west-2",
            imageId="ami-c",
        )
    )
    db.commit()

    result = crud.latest_aws_image(db, None)
    assert result["arm64"]["name"] == "test_image_2b"
    assert result["arm64"]["amis"] == {"us-west-1": "ami-2b", "us-west-2": "ami-c"}


def test_latest_aws_image_query_for_arch(db):
    images = [
        AwsImage(
            id="ami-1a",
            name="test_image_1a",
            arch="x86_64",
            version="1.0",
            date=datetime.strptime("2022-01-01", "%Y-%m-%d").date(),
            region="us-west-1",
            imageId="ami-1a",
        ),
        AwsImage(
            id="ami-1b",
            name="test_image_1b",
            arch="x86_64",
            version="2.0",
            date=datetime.strptime("2022-01-01", "%Y-%m-%d").date(),
            region="us-west-1",
            imageId="ami-1b",
        ),
        AwsImage(
            id="ami-2a",
            name="test_image_2a",
            arch="arm64",
            version="1.0",
            date=datetime.strptime("2022-01-01", "%Y-%m-%d").date(),
            region="us-west-1",
            imageId="ami-2a",
        ),
        AwsImage(
            id="ami-2b",
            name="test_image_2b",
            arch="arm64",
            version="2.0",
            date=datetime.strptime("2022-01-01", "%Y-%m-%d").date(),
            region="us-west-1",
            imageId="ami-2b",
        ),
    ]

    db.add_all(images)
    db.commit()

    result = crud.latest_aws_image(db, "x86_64")
    assert result["x86_64"]["name"] == "test_image_1b"
    assert result["x86_64"]["amis"] == {"us-west-1": "ami-1b"}
    assert "arm64" not in result


def test_latest_azure_image_no_images(db):
    result = crud.latest_azure_image(db, None)
    assert result == {"error": "No images found for Azure", "code": 404}


def test_latest_azure_image_wrong_arch(db):
    result = crud.latest_azure_image(db, "arm32")
    assert result == {"error": "No images found for Azure", "code": 404}


def test_latest_azure_image_single_arch(db):
    images = [
        AzureImage(
            id="urn-a",
            architecture="arm64",
            sku="sku-a",
            offer="offer-a",
            version="1.0",
            urn="urn-a",
        ),
        AzureImage(
            id="urn-b",
            architecture="arm64",
            sku="sku-a",
            offer="offer-a",
            version="2.0",
            urn="urn-b",
        ),
    ]
    db.add_all(images)
    db.commit()

    result = crud.latest_azure_image(db, None)
    print(result)
    assert result["arm64"]["sku"] == "sku-a"
    assert result["arm64"]["version"] == "2.0"


def test_latest_azure_image_multiple_arch(db):
    images = [
        AzureImage(
            id="urn-1a",
            architecture="arm64",
            sku="sku-1a",
            offer="offer-1a",
            version="1.0",
            urn="urn-1a",
        ),
        AzureImage(
            id="urn-2a",
            architecture="arm64",
            sku="sku-2a",
            offer="offer-2a",
            version="1.5",
            urn="urn-2a",
        ),
        AzureImage(
            id="urn-1b",
            architecture="x64",
            sku="sku-1b",
            offer="offer-1b",
            version="2.0",
            urn="urn-1b",
        ),
        AzureImage(
            id="urn-2b",
            architecture="x64",
            sku="sku-2b",
            offer="offer-2b",
            version="1.0",
            urn="urn-2b",
        ),
    ]
    db.add_all(images)
    db.commit()

    result = crud.latest_azure_image(db, None)
    assert result["arm64"]["sku"] == "sku-2a"
    assert result["arm64"]["version"] == "1.5"
    assert result["x64"]["sku"] == "sku-1b"
    assert result["x64"]["version"] == "2.0"


def test_latest_azure_image_query_arch(db):
    images = [
        AzureImage(
            id="urn-1a",
            architecture="arm64",
            sku="sku-1a",
            offer="offer-1a",
            version="1.0",
            urn="urn-1a",
        ),
        AzureImage(
            id="urn-2a",
            architecture="arm64",
            sku="sku-2a",
            offer="offer-2a",
            version="1.5",
            urn="urn-2a",
        ),
        AzureImage(
            id="urn-1b",
            architecture="x64",
            sku="sku-1b",
            offer="offer-1b",
            version="2.0",
            urn="urn-1b",
        ),
        AzureImage(
            id="urn-2b",
            architecture="x64",
            sku="sku-2b",
            offer="offer-2b",
            version="1.0",
            urn="urn-2b",
        ),
    ]
    db.add_all(images)
    db.commit()

    result = crud.latest_azure_image(db, "x64")
    assert result["x64"]["sku"] == "sku-1b"
    assert result["x64"]["version"] == "2.0"
    assert "arm64" not in result


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

    assert db.query(AwsImage).count() == 500
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


def test_find_available_aws_versions(db):
    images = [
        AwsImage(id="ami-a", version="8.2.0"),
        AwsImage(id="ami-b", version="7.9.0"),
        AwsImage(id="ami-c", version="9.5.0"),
        AwsImage(id="ami-d", version="10.0.0"),
        AwsImage(id="ami-e", version="9.5.0"),
    ]
    db.add_all(images)
    db.commit()

    result = crud.find_available_aws_versions(db)
    assert result == ["10.0.0", "9.5.0", "8.2.0", "7.9.0"]


def test_find_available_azure_versions(db):
    images = [
        AzureImage(id="urn-a", version="8.2.2023122216"),
        AzureImage(id="urn-b", version="7.9.2023122216"),
        AzureImage(id="urn-c", version="9.5.2023122216"),
        AzureImage(id="urn-d", version="10.0.2023122216"),
        AzureImage(id="urn-e", version="9.5.2023122216"),
    ]
    db.add_all(images)
    db.commit()

    result = crud.find_available_azure_versions(db)
    assert result == ["10.0", "9.5", "8.2", "7.9"]


def test_find_available_google_versions(db):
    images = [
        GoogleImage(id="id-a", version="8.2.0"),
        GoogleImage(id="id-b", version="7.9.0"),
        GoogleImage(id="id-c", version="9.5.0"),
        GoogleImage(id="id-d", version="10.0.0"),
        GoogleImage(id="id-e", version="9.5.0"),
    ]
    db.add_all(images)
    db.commit()

    result = crud.find_available_google_versions(db)
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
