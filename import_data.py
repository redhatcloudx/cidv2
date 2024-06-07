import argparse
import json
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cid.config import DATABASE_URL
from cid.models import AwsImage, AzureImage, Base, GoogleImage


def load_data(file_path):
    with open(file_path) as file:
        return json.load(file)


def extract_aws_version(image_name: str) -> str:
    match = re.search(r"\d+\.\d+(\.\d+)?", image_name)
    return match.group() if match else None


def extract_google_version(name):
    match = re.search(r"\d+(\-\d+)?", name)
    if match:
        version = match.group()
        return version.replace("-", ".") if "-" in version else version
    return None


def import_aws_data(images):
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Drop the AwsImage table
    AwsImage.__table__.drop(engine, checkfirst=True)

    # Recreate the AwsImage table
    Base.metadata.tables["aws_images"].create(engine)

    for image in images:
        image_obj = AwsImage(
            id=image.get("ImageId"),
            name=image.get("Name"),
            arch=image.get("Architecture"),
            version=extract_aws_version(image.get("Name")),
            imageId=image.get("ImageId"),
            date=image.get("CreationDate"),
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
            deprecationTime=image.get("DeprecationTime"),
        )
        session.add(image_obj)
    session.commit()


def import_azure_data(images):
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Drop the AzureImage table
    AzureImage.__table__.drop(engine, checkfirst=True)

    # Recreate the AzureImage table
    Base.metadata.tables["azure_images"].create(engine)

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
        session.add(image_obj)
    session.commit()


def import_google_data(images):
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Drop the GoogleImage table
    GoogleImage.__table__.drop(engine, checkfirst=True)

    # Recreate the GoogleImage table
    Base.metadata.tables["google_images"].create(engine)

    for image in images:
        image_obj = GoogleImage(
            id=image.get("id"),
            name=image.get("name"),
            arch=image.get("architecture"),
            version=extract_google_version(image.get("name")),
            creationTimestamp=image.get("creationTimestamp"),
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
        session.add(image_obj)
    session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("provider", help="The cloud provider (aws, google, azure)")
    parser.add_argument(
        "file_path", help="The path to the JSON file containing the images"
    )
    args = parser.parse_args()

    images = load_data(args.file_path)
    if args.provider == "aws":
        import_aws_data(images)
    elif args.provider == "google":
        import_google_data(images)
    elif args.provider == "azure":
        import_azure_data(images)
    else:
        print(f"Unknown provider: {args.provider}")
