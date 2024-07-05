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


app = FastAPI()


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


@app.get("/")
def read_root(request: Request, db: Session = Depends(get_db)) -> dict:  # noqa: B008
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


@app.get("/aws")
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
    result = crud.find_aws_images(
        db, arch, version, name, region, image_id, page, page_size
    )
    return dict(jsonable_encoder(result))


@app.get("/aws/latest")
def latest_aws_image(db: Session = Depends(get_db), arch: Optional[str] = None) -> dict:  # noqa: B008
    return crud.latest_aws_image(db, arch)


@app.get("/aws/match/{image_id}")
def match_aws_image(image_id: str, db: Session = Depends(get_db)) -> dict:  # noqa: B008
    result = crud.find_matching_ami(db, image_id)
    return result


@app.get("/azure")
def all_azure_images(
    db: Session = Depends(get_db),  # noqa: B008
    arch: Optional[str] = None,
    version: Optional[str] = None,
    urn: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
) -> dict:
    result = crud.find_azure_images(db, arch, version, urn, page, page_size)
    return dict(jsonable_encoder(result))


@app.get("/azure/latest")
def latest_azure_image(
    db: Session = Depends(get_db),  # noqa: B008
    arch: Optional[str] = None,
) -> dict:
    return crud.latest_azure_image(db, arch)


@app.get("/google/latest")
def latest_google_image(
    db: Session = Depends(get_db),  # noqa: B008
    arch: Optional[str] = None,
) -> dict:
    return crud.latest_google_image(db, arch)


@app.get("/aws/versions")
def aws_versions(db: Session = Depends(get_db)) -> list:  # noqa: B008
    return crud.find_available_aws_versions(db)


@app.get("/azure/versions")
def azure_versions(db: Session = Depends(get_db)) -> list:  # noqa: B008
    return crud.find_available_azure_versions(db)


@app.get("/google")
def all_google_images(
    db: Session = Depends(get_db),  # noqa: B008
    arch: Optional[str] = None,
    version: Optional[str] = None,
    name: Optional[str] = None,
    family: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
) -> dict:
    result = crud.find_google_images(db, arch, version, name, family, page, page_size)
    return dict(jsonable_encoder(result))


@app.get("/google/versions")
def google_versions(db: Session = Depends(get_db)) -> list:  # noqa: B008
    return crud.find_available_google_versions(db)


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
