"""Tests for the utilities."""

import pytest

from cid import utils
from cid.config import AWS_IMAGE_DATA, AZURE_IMAGE_DATA, GCP_IMAGE_DATA

AWS_IMAGES = [
    ("RHEL-9.2.0_HVM-20231115-arm64-23-Hourly2-GP3", "9.2.0"),
    ("RHEL_HA-9.0.0_HVM-20231003-x86_64-16-Hourly2-GP2", "9.0.0"),
    ("RHEL-SAP-8.2.0_HVM-20230117-x86_64-9-Hourly2-GP2", "8.2.0"),
    ("RHEL-7.9_HVM-20211005-x86_64-0-Hourly2-GP2", "7.9"),
]

GOOGLE_IMAGES = [
    ("rhel-7-v20240515", "7"),
    ("rhel-8-v20240515", "8"),
    ("rhel-9-arm64-v20240515", "9.arm64"),
    ("rhel-9-v20240515", "9"),
]


def test_get_json_data(httpx_mock):
    """Test the get_json_data function."""
    httpx_mock.add_response(
        url=AWS_IMAGE_DATA,
        json=[{"cloud": "aws"}],
    )
    httpx_mock.add_response(
        url=AZURE_IMAGE_DATA,
        json=[{"cloud": "azure"}],
    )
    httpx_mock.add_response(
        url=GCP_IMAGE_DATA,
        json=[{"cloud": "gcp"}],
    )

    assert utils.get_json_data("aws")[0] == {"cloud": "aws"}
    assert utils.get_json_data("azure")[0] == {"cloud": "azure"}
    assert utils.get_json_data("gcp")[0] == {"cloud": "gcp"}

    with pytest.raises(utils.InvalidCloudProvider):
        utils.get_json_data("Gewitter")


@pytest.mark.parametrize("image_name,expected", GOOGLE_IMAGES)
def test_extract_google_version(image_name, expected):
    """Test the extract_google_version function."""
    version = utils.extract_google_version(image_name)
    assert version == expected


@pytest.mark.parametrize("image_name,expected", AWS_IMAGES)
def test_extract_aws_version(image_name, expected):
    """Test the extract_aws_version function."""
    version = utils.extract_aws_version(image_name)
    assert version == expected
