import logging
import threading
from time import sleep
from typing import Any, Generator, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from schedule import every, repeat, run_pending
from sqlalchemy.orm import Session

from cid import crud
from cid.config import ENVIRONMENT
from cid.database import SessionLocal

log = logging.getLogger(__name__)

description = """
## 🚧 Experimental API

This API remains under active development and may change substantially at any time.

You can access API documentation via [Swagger](/docs) as well as [Redocly](/redoc).

Please send any questions or comments to the
[Cloud Experience Team at Red Hat](mailto:cloudexperience@redhat.com)
or submit a [GitHub issue](https://github.com/redhatcloudx/cidv2).

----
"""

app = FastAPI(
    title="CIDv2",
    description=description,
    summary="🔎 Find Red Hat Enterprise Linux™ images on various cloud providers.",
    version="2.0.0dev",
    contact={
        "name": "Red Hat's Cloud Experience Team",
        "url": "https://github.com/redhatcloudx/",
        "email": "cloudexperience@redhat.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_endpoint_status(
    db: Session, endpoint_func: Any, *args: str, **kwargs: int
) -> str:
    try:
        data = endpoint_func(db, *args, **kwargs)
        if data is None:
            return "down"
        else:
            return "running"
    except HTTPException:
        return "down"


@app.get("/", summary="Status")
def status(request: Request, db: Session = Depends(get_db)) -> dict:  # noqa: B008
    """
    Get the status of the CIDv2 API and the last update time.
    """
    aws_status = check_endpoint_status(db, crud.find_aws_images, page=1, page_size=1)
    google_status = check_endpoint_status(
        db, crud.find_google_images, page=1, page_size=1
    )
    azure_status = check_endpoint_status(
        db, crud.find_azure_images, page=1, page_size=1
    )
    last_update = crud.get_last_update(db)
    return {
        "status": {
            f"{request.base_url}aws": aws_status,
            f"{request.base_url}google": google_status,
            f"{request.base_url}azure": azure_status,
        },
        "docs": f"{request.base_url}docs",
        "last_update": last_update,
    }


@app.get("/aws", summary="AWS: Get all images")
def all_aws_images(
    db: Session = Depends(get_db),  # noqa: B008
    arch: Optional[str] = None,
    version: Optional[str] = None,
    name: Optional[str] = None,
    region: Optional[str] = None,
    image_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
) -> dict:
    """
    Get a list of all of the Red Hat Enterprise Linux™ images from AWS.

    - **arch**: Limit results to a single architecture, such as `arm64` or `x86_64`.
    - **image_id**: Search for images by ImageId.
    - **name**: Search for images by name.
    - **page**: The page number to return.
    - **page_size**: The number of results to return per page.
    - **region**: Limit results to a specific AWS region such as `us-east-1`.
    - **version**: Search for a specific RHEL version such as `8.8` or `9.4`.
    """
    result = crud.find_aws_images(
        db, arch, version, name, region, image_id, page, page_size
    )
    return dict(jsonable_encoder(result))


@app.get("/aws/versions", summary="AWS: Get available versions")
def aws_versions(db: Session = Depends(get_db)) -> list:  # noqa: B008
    """
    Get a list of Red Hat Enterprise Linux™ versions which are available to deploy in AWS.
    """
    return crud.find_available_aws_versions(db)


@app.get("/aws/latest", summary="AWS: Get latest image")
def latest_aws_image(db: Session = Depends(get_db), arch: Optional[str] = None) -> dict:  # noqa: B008
    """
    Get the latest Red Hat Enterprise Linux™ image from AWS in each region.

    - **arch**: Limit results to a single architecture, such as `arm64` or `x86_64`.
    """
    return crud.latest_aws_image(db, arch)


@app.get("/aws/match/{image_id}", summary="AWS: Match image")
def match_aws_image(image_id: str, db: Session = Depends(get_db)) -> dict:  # noqa: B008
    """
    Find other Red Hat Enterprise Linux™ images from other AWS regions that match the
    `image_id` provided.

    - **image_id**: AWS ImageId to match in other regions.
    """
    result = crud.find_matching_ami(db, image_id)
    return result


@app.get("/azure", summary="Azure: Get all images")
def all_azure_images(
    db: Session = Depends(get_db),  # noqa: B008
    arch: Optional[str] = None,
    version: Optional[str] = None,
    urn: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
) -> dict:
    """
    Get a list of all of the Red Hat Enterprise Linux™ images available in Azure.

    - **arch**: Limit results to a single architecture, such as `arm64` or `x64`.
    - **page**: The page number to return.
    - **page_size**: The number of results to return per page.
    - **urn**: Limit results to a specific Azure URN.
    - **version**: Search for a specific RHEL version such as `8.8` or `9.4`.
    """
    result = crud.find_azure_images(db, arch, version, urn, page, page_size)
    return dict(jsonable_encoder(result))


@app.get("/azure/versions", summary="Azure: Get available versions")
def azure_versions(db: Session = Depends(get_db)) -> list:  # noqa: B008
    """
    Get a list of Red Hat Enterprise Linux™ versions which are available to deploy in Azure.
    """
    return crud.find_available_azure_versions(db)


@app.get("/azure/latest", summary="Azure: Get latest image")
def latest_azure_image(
    db: Session = Depends(get_db),  # noqa: B008
    arch: Optional[str] = None,
) -> dict:
    """
    Get the latest Red Hat Enterprise Linux™ image from Azure.

    - **arch**: Limit results to a single architecture, such as `arm64` or `x64`.
    """
    return crud.latest_azure_image(db, arch)


@app.get("/google", summary="Google: Get all images")
def all_google_images(
    db: Session = Depends(get_db),  # noqa: B008
    arch: Optional[str] = None,
    version: Optional[str] = None,
    name: Optional[str] = None,
    family: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
) -> dict:
    """
    Get a list of all of the Red Hat Enterprise Linux™ images available in Google Cloud Platform.

    - **arch**: Limit results to a single architecture, such as `ARM64` or `X86_64`.
    - **name**: Search for images by name.
    - **family**: Search for images by family.
    - **page**: The page number to return.
    - **page_size**: The number of results to return per page.
    - **urn**: Limit results to a specific Azure URN.
    - **version**: Search for a specific RHEL version such as `8.8` or `9.4`.
    """
    result = crud.find_google_images(db, arch, version, name, family, page, page_size)
    return dict(jsonable_encoder(result))


@app.get("/google/versions", summary="Google: Get available versions")
def google_versions(db: Session = Depends(get_db)) -> list:  # noqa: B008
    """
    Get a list of Red Hat Enterprise Linux™ versions which are available to deploy in Google Cloud Platform.
    """
    return crud.find_available_google_versions(db)


@app.get("/google/latest", summary="Google: Get latest image")
def latest_google_image(
    db: Session = Depends(get_db),  # noqa: B008
    arch: Optional[str] = None,
) -> dict:
    """
    Get the latest Red Hat Enterprise Linux™ image from Google Cloud Platform.

    - **arch**: Limit results to a single architecture, such as `ARM64` or `X86_64`.
    """
    return crud.latest_google_image(db, arch)


@repeat(every(24).hours)
def self_update_image_data() -> None:
    """Update the database with new image data."""
    db = SessionLocal()
    crud.update_image_data(db)
    crud.update_last_updated(db)


def run_schedule() -> None:
    """Background task to run the scheduled tasks."""
    while True:
        run_pending()
        sleep(1)


# Run the schedule in a separate thread
# NOTE(major): Pytest runs this code for some reason. This is a workaround.
if ENVIRONMENT != "testing":
    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.start()
