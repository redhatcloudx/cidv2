import argparse
import json
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cid.models import AwsImage, Base  # , AzureImage, GoogleImage

engine = create_engine("postgresql://postgres:postgres@db:5432/test_db")
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)


def load_data(file_path):
    with open(file_path) as file:
        return json.load(file)


def extract_version(image_name: str) -> str:
    match = re.search(r"\d+\.\d+(\.\d+)?", image_name)
    return match.group() if match else None


def import_aws_data(images):
    session = Session()
    for image in images:
        image_obj = AwsImage(
            name=image.get("Name"),
            arch=image.get("Architecture"),
            version=extract_version(image.get("Name")),
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("provider", help="The cloud provider (aws, google, azure)")
    args = parser.parse_args()

    images = load_data("data.json")
    if args.provider == "aws":
        import_aws_data(images)
    # elif args.provider == 'google':
    #     import_google_data(images)
    # elif args.provider == 'azure':
    #     import_azure_data(images)
    else:
        print(f"Unknown provider: {args.provider}")
