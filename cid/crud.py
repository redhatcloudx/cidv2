"""Create, replace, update, and delete functions for the CID database."""

import logging
from typing import Any, Optional

from dateutil import parser
from packaging.version import Version
from sqlalchemy import desc
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query

from cid.config import CLOUD_PROVIDERS
from cid.database import engine
from cid.models import AwsImage, AzureImage, GoogleImage
from cid.utils import (
    InvalidCloudProvider,
    extract_aws_version,
    extract_google_version,
    get_json_data,
)

logger = logging.getLogger(__name__)


def aws_regions(db: Session) -> list:
    """Get all AWS regions."""
    return db.query(AwsImage.region).distinct().order_by(AwsImage.region).all()


def latest_aws_image(db: Session, arch: Optional[str]) -> dict[str, Any]:
    """Get the latest RHEL image on AWS."""
    archs = (
        [arch]
        if arch is not None
        else [arch[0] for arch in db.query(AwsImage.arch).distinct().all()]
    )

    latest_images_dict = {}
    for arch in archs:
        # Find the image with the highest version number and the latest date.
        latest_image = (
            db.query(AwsImage)
            .filter(AwsImage.name.notlike("%BETA%"), AwsImage.arch == arch)
            .order_by(desc(AwsImage.version), desc(AwsImage.date))
            .first()
        )
        if latest_image is None:
            continue

        # Loop through each region to find the latest image available in each.
        images = {}
        for region in aws_regions(db):
            region_image = (
                db.query(AwsImage)
                .filter(
                    AwsImage.region == region[0],
                    AwsImage.name == latest_image.name,
                    AwsImage.arch == arch,
                )
                .first()
            )
            if region_image is not None:
                images[region[0]] = region_image.imageId

        latest_images_dict[arch] = {
            "name": latest_image.name,
            "version": latest_image.version,
            "date": latest_image.date,
            "amis": images,
        }

    if not latest_images_dict:
        return {"error": "No images found for AWS.", "code": 404}

    return latest_images_dict


def latest_azure_image(db: Session, arch: Optional[str]) -> dict[str, Any]:
    """Get the latest RHEL image on Azure."""
    archs = (
        [arch]
        if arch is not None
        else [arch[0] for arch in db.query(AzureImage.architecture).distinct().all()]
    )
    latest_images_dict = {}
    for arch in archs:
        latest_image = (
            db.query(AzureImage)
            .filter(AzureImage.architecture == arch)
            .order_by(desc(AzureImage.version))
            .first()
        )

        if latest_image is None:
            continue

        latest_images_dict[arch] = {
            "sku": latest_image.sku,
            "offer": latest_image.offer,
            "version": latest_image.version,
            "urn": latest_image.urn,
        }

    if not latest_images_dict:
        return {"error": "No images found for Azure", "code": 404}

    return latest_images_dict


def latest_google_image(db: Session, arch: Optional[str]) -> dict:
    """Get the latest RHEL image on Google Cloud."""
    archs = (
        [arch]
        if arch is not None
        else [arch[0] for arch in db.query(GoogleImage.arch).distinct().all()]
    )
    latest_images_dict = {}
    for arch in archs:
        latest_image = (
            db.query(GoogleImage)
            .filter(GoogleImage.arch.ilike(arch))
            .order_by(desc(GoogleImage.version), desc(GoogleImage.creationTimestamp))
            .first()
        )

        if latest_image is None:
            return {"error": "No images found for Google Cloud", "code": 404}

        latest_images_dict[arch] = {
            "name": latest_image.name,
            "version": latest_image.version,
            "date": latest_image.creationTimestamp,
            "selfLink": latest_image.selfLink,
        }

    if not latest_images_dict:
        return {"error": "No images found for Google Cloud", "code": 404}

    return latest_images_dict


def import_aws_images(db: Session, images: list) -> None:
    """Take a list of AWS images and add them to the database."""
    import_queue = []

    for image in images:
        # sqlite requires dates to be in Python's datetime format.
        creation_date = parser.parse(image.get("CreationDate"))
        deprecation_time = parser.parse(image.get("DeprecationTime"))

        # Extract the RHEL version number from the image name.
        image_name = extract_aws_version(image.get("Name"))

        # AWS has a LOT of data. We generate a list of dictionaries and then
        # import them in bulk at the end.
        image_dict = {
            "id": image.get("ImageId"),
            "name": image.get("Name"),
            "arch": image.get("Architecture"),
            "version": image_name,
            "imageId": image.get("ImageId"),
            "date": creation_date,
            "provider": image.get("ImageOwnerAlias"),
            "region": image.get("Region"),
            "description": image.get("Description"),
            "creationDate": creation_date,
            "deprecationTime": deprecation_time,
        }
        import_queue.append(image_dict)

    logger.info("Adding %s AWS images to the database", len(import_queue))

    # This lower-level method is more efficient for inserting lots of rows at once.
    db.execute(AwsImage.__table__.insert(), import_queue)
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
        creation_timestamp = parser.parse(image.get("creationTimestamp"))

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


def update_image_data(db: Session) -> None:
    """Update image data from all cloud providers."""

    # Ensure all tables are created. This is skipped if the tables exist.
    AwsImage.metadata.create_all(bind=engine)
    AzureImage.metadata.create_all(bind=engine)
    GoogleImage.metadata.create_all(bind=engine)

    # Truncate all tables before importing new data.
    db.query(AwsImage).delete()
    db.query(AzureImage).delete()
    db.query(GoogleImage).delete()

    for cloud in CLOUD_PROVIDERS:
        logger.info("⬇️ Downloading cloud image data for %s", cloud)
        data = get_json_data(cloud)

        logger.info("🔄 Updating database with new cloud image data for %s", cloud)
        match cloud:
            case "aws":
                import_aws_images(db, data)
            case "azure":
                import_azure_images(db, data)
            case "google":
                import_google_images(db, data)
            case _:
                raise InvalidCloudProvider(cloud)

    logger.info("🎉 Image data updated successfully")


def find_matching_ami(db: Session, image_id: str) -> dict:
    """Given a single AMI, find matching AMIs in other regions.

    Args:
        db (Session): database session
        image_id (str): AMI ID to search

    Returns:
        dict: basic information about the image with matching AMIs
    """
    # Get the image record for the AMI we were given.
    image = db.query(AwsImage).filter(AwsImage.imageId == image_id).first()

    if image is None:
        return {"error": "No images found", "code": 404}

    # Use the name to find matching images in other regions.
    matching_images = (
        db.query(AwsImage.imageId, AwsImage.region)
        .filter(AwsImage.name == image.name)
        .all()
    )

    return {
        "ami": image.imageId,
        "name": image.name,
        "version": image.version,
        "region": image.region,
        "matching_images": [
            {"region": region, "ami": imageId} for imageId, region in matching_images
        ],
    }


def find_available_aws_versions(db: Session) -> list:
    """Return all RHEL versions available from AWS.

    It would be good to add the other providers later, but this data is so much easier
    to gather on AWS right now.

    Args:
        db (Session): database session name
        (str): image name to search

    Returns:
        list: list of available versions
    """
    # Get all images with the given name.
    versions = [x.version for x in db.query(AwsImage.version).distinct()]

    return sorted(versions, key=Version, reverse=True)


def find_available_azure_versions(db: Session) -> list:
    """Return all RHEL versions available from Azure.

    Args:
        db (Session): database session name
    Returns:
        list: list of available versions
    """
    query = db.query(AzureImage.version).distinct()

    versions = [".".join(x.version.split(".")[:2]) for x in query]
    versions = list(set(versions))

    return sorted(versions, key=Version, reverse=True)


def find_available_google_versions(db: Session) -> list:
    """Return all RHEL versions available from Google Cloud.

    Args:
        db (Session): database session name
    Returns:
        list: list of available versions
    """
    versions = [x.version for x in db.query(GoogleImage.version).distinct()]

    def version_key(version: str) -> Version:
        parts = [part for part in version.split(".") if part.isdigit()]
        return Version(".".join(parts))

    return sorted(versions, key=version_key, reverse=True)


def find_images_for_version(db: Session, version: str) -> list:
    """Return all images for a specific version of RHEL.

    Args:
        db (Session): database session
        version (str): RHEL version to search

    Returns:
        list: list of images for the given version
    """
    images = db.query(AwsImage).filter(AwsImage.version == version).all()

    for image in images:
        print(image.id)

    return [{"ami": x.id, "name": x.name} for x in images]


def find_aws_images(
    db: Session,
    arch: Optional[str] = None,
    version: Optional[str] = None,
    name: Optional[str] = None,
    region: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
) -> dict:
    """Return paginated AWS images that match the given criteria.

    Args:
      db (Session): database session
      arch (Optional[str]): architecture to search
      version (Optional[str]): RHEL version to search
      name (Optional[str]): image name to search
      region (Optional[str]): AWS region to search
      page (int): page number
      page_size (int): number of images per page

    Returns:
      list: list of images that match the given criteria
    """
    query = db.query(AwsImage).order_by(AwsImage.creationDate.desc())

    if arch:
        query = query.filter(AwsImage.arch == arch)
    if version:
        query = query.filter(AwsImage.version == version)
    if name:
        query = query.filter(AwsImage.name.contains(name))
    if region:
        query = query.filter(AwsImage.region == region)

    return paginate(query, page, page_size)


def paginate(
    query: Query,
    page: int = 1,
    page_size: int = 100,
) -> dict:
    """Paginate a query and return the results.

    Args:
      query: SQLAlchemy query object
      page (int): page number
      page_size (int): number of items per page

    Returns:
      dict: paginated results
    """
    if page < 1:
        page = 1

    if page_size < 1:
        page_size = 1

    total_count = query.count()
    total_pages = (total_count + page_size - 1) // page_size

    results = query.limit(page_size).offset((page - 1) * page_size).all()

    return {
        "results": results,
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": total_pages,
    }
