"""Create, replace, update, and delete functions for the CID database."""

from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from cid.models import AwsImage, AzureImage, GoogleImage


def aws_regions(db: Session) -> list:
    """Get all AWS regions."""
    return db.query(AwsImage.region).distinct().order_by(AwsImage.region).all()


def latest_aws_image(db: Session) -> dict[str, Any]:
    """Get the latest RHEL image on AWS."""
    # Find the image with the highest version number and the latest date.
    latest_image = (
        db.query(AwsImage).order_by(desc(AwsImage.version), desc(AwsImage.date)).first()
    )

    if latest_image is None:
        return {"error": "No images found", "code": 404}

    # Loop through each region to find the latest image available in each.
    images = {}
    for region in aws_regions(db):
        region_image = (
            db.query(AwsImage)
            .filter(AwsImage.region == region[0], AwsImage.name == latest_image.name)
            .first()
        )
        if region_image is not None:
            images[region[0]] = region_image.imageId

    return {
        "name": latest_image.name,
        "version": latest_image.version,
        "date": latest_image.date,
        "amis": images,
    }


def latest_azure_image(db: Session) -> dict[str, Any]:
    """Get the latest RHEL image on Azure."""
    latest_image = db.query(AzureImage).order_by(desc(AzureImage.version)).first()

    if latest_image is None:
        return {"error": "No images found", "code": 404}

    return {
        "sku": latest_image.sku,
        "offer": latest_image.offer,
        "version": latest_image.version,
        "urn": latest_image.urn,
    }


def latest_google_image(db: Session) -> dict:
    """Get the latest RHEL image on Google Cloud."""
    latest_image = (
        db.query(GoogleImage)
        .order_by(desc(GoogleImage.version), desc(GoogleImage.creationTimestamp))
        .first()
    )

    if latest_image is None:
        return {"error": "No images found", "code": 404}

    return {
        "name": latest_image.name,
        "version": latest_image.version,
        "date": latest_image.creationTimestamp,
        "selfLink": latest_image.selfLink,
    }
