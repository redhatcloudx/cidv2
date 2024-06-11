"""General utilities for the CID package."""

import logging
import re

import httpx

from cid.config import AWS_IMAGE_DATA, AZURE_IMAGE_DATA, GCP_IMAGE_DATA

logger = logging.getLogger(__name__)


class InvalidCloudProvider(Exception):
    """When an invalid cloud provider is provided."""

    pass


def get_json_data(cloud_provider: str) -> list[dict]:
    """Get image data from the retriever."""
    match cloud_provider:
        case "aws":
            data_url = AWS_IMAGE_DATA
        case "azure":
            data_url = AZURE_IMAGE_DATA
        case "gcp":
            data_url = GCP_IMAGE_DATA
        case _:
            raise InvalidCloudProvider(cloud_provider)
    response = httpx.get(data_url)
    return list(response.json()) if response.json() else []


def extract_aws_version(image_name: str) -> str:
    """Extract the RHEL version from an AWS image name."""
    match = re.search(r"\d+\.\d+(\.\d+)?", image_name)
    return str(match.group()) if match else ""


def extract_google_version(image_name: str) -> str:
    """Extract the RHEL version from a Google image name."""
    match = re.findall(r"rhel-(\d{1,2}(?:-arm64)*)", image_name)
    return str(match[0].replace("-", ".")) if match else ""
