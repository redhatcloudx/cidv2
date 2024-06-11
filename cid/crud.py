"""Create, replace, update, and delete functions for the CID database."""

from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from cid.models import AwsImage


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
