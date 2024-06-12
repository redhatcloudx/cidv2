"""Create, replace, update, and delete functions for the CID database."""

import logging
from typing import Any

import dateparser
from sqlalchemy import desc
from sqlalchemy.orm import Session

from cid.models import AwsImage, AzureImage, GoogleImage
from cid.utils import extract_aws_version, extract_google_version

logger = logging.getLogger(__name__)


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


def import_aws_images(db: Session, images: list) -> None:
    """Take a list of AWS images and add them to the database."""
    import_queue = []

    for image in images:
        # sqlite requires dates to be in Python's datetime format.
        creation_date = dateparser.parse(image.get("CreationDate"))
        deprecation_time = dateparser.parse(image.get("DeprecationTime"))

        # Extract the RHEL version number from the image name.
        image_name = extract_aws_version(image.get("Name"))

        image_obj = AwsImage(
            id=image.get("ImageId"),
            name=image.get("Name"),
            arch=image.get("Architecture"),
            version=image_name,
            imageId=image.get("ImageId"),
            date=creation_date,
            virt=image.get("VirtualizationType"),
            provider=image.get("ImageOwnerAlias"),
            region=image.get("Region"),
            imageLocation=image.get("ImageLocation"),
            imageType=image.get("ImageType"),
            public=image.get("Public"),
            ownerId=image.get("OwnerId"),
            platformDetails=image.get("PlatformDetails"),
            usageOperation=image.get("UsageOperation"),
            state=image.get("State"),
            blockDeviceMappings=image.get("BlockDeviceMappings"),
            description=image.get("Description"),
            enaSupport=image.get("EnaSupport"),
            hypervisor=image.get("Hypervisor"),
            rootDeviceName=image.get("RootDeviceName"),
            rootDeviceType=image.get("RootDeviceType"),
            sriovNetSupport=image.get("SriovNetSupport"),
            deprecationTime=deprecation_time,
        )
        import_queue.append(image_obj)

    logger.info("Adding %s AWS images to the database", len(import_queue))

    db.add_all(import_queue)
    db.commit()


def import_azure_images(db: Session, images: list) -> None:
    """Take a list of Azure images and add them to the database."""
    import_queue = []

    for image in images:
        image_obj = AzureImage(
            id=image.get("urn"),
            architecture=image.get("architecture"),
            offer=image.get("offer"),
            publisher=image.get("publisher"),
            sku=image.get("sku"),
            urn=image.get("urn"),
            version=image.get("version"),
        )
        import_queue.append(image_obj)

    logger.info("Adding %s Azure images to the database", len(import_queue))

    db.add_all(import_queue)
    db.commit()


def import_google_images(db: Session, images: list) -> None:
    """Take a list of Google images and add them to the database."""
    import_queue = []

    for image in images:
        # sqlite requires dates to be in Python's datetime format.
        creation_timestamp = dateparser.parse(image.get("creationTimestamp"))

        # Extract the RHEL version number from the image name.
        image_name = extract_google_version(image.get("name"))

        image_obj = GoogleImage(
            id=image.get("id"),
            name=image.get("name"),
            arch=image.get("architecture"),
            version=image_name,
            creationTimestamp=creation_timestamp,
            description=image.get("description"),
            diskSizeGb=image.get("diskSizeGb"),
            family=image.get("family"),
            guestOsFeatures=image.get("guestOsFeatures"),
            kind=image.get("kind"),
            labelFingerprint=image.get("labelFingerprint"),
            licenseCodes=image.get("licenseCodes"),
            licenses=image.get("licenses"),
            rawDisk=image.get("rawDisk"),
            selfLink=image.get("selfLink"),
            sourceType=image.get("sourceType"),
            status=image.get("status"),
            storageLocations=image.get("storageLocations"),
        )
        import_queue.append(image_obj)

    logger.info("Adding %s Google images to the database", len(import_queue))

    db.add_all(import_queue)
    db.commit()
