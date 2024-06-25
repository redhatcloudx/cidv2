import logging
import threading
from time import sleep
from typing import Any, Dict, Generator, Optional

from fastapi import Depends, FastAPI
from fastapi.encoders import jsonable_encoder
from schedule import every, repeat, run_all, run_pending
from sqlalchemy.orm import Session

from cid import crud
from cid.config import ENVIRONMENT
from cid.database import SessionLocal
from cid.models import AwsImage
from cid.utils import wait_for_database

log = logging.getLogger(__name__)

app = FastAPI()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root() -> dict:
    return {"Hello": "World"}


@app.get("/latest")
def latest(db: Session = Depends(get_db)) -> Dict[str, Any]:  # noqa: B008
    return {
        "latest_aws_image": crud.latest_aws_image(db),
        "latest_azure_image": crud.latest_azure_image(db, None),
        "latest_google_image": crud.latest_google_image(db),
    }


@app.get("/aws")
def all_aws_images(db: Session = Depends(get_db)) -> list:  # noqa: B008
    result = db.query(AwsImage).order_by(AwsImage.creationDate.desc()).all()
    return list(jsonable_encoder(result))


@app.get("/aws/{image_id}")
def single_aws_image(image_id: str, db: Session = Depends(get_db)) -> dict:  # noqa: B008
    result = db.query(AwsImage).filter(AwsImage.id == image_id).first()
    return dict(jsonable_encoder(result))


@app.get("/aws/match/{image_id}")
def match_aws_image(image_id: str, db: Session = Depends(get_db)) -> dict:  # noqa: B008
    result = crud.find_matching_ami(db, image_id)
    return result


@app.get("/azure/latest")
def latest_azure_image(
    db: Session = Depends(get_db),  # noqa: B008
    arch: Optional[str] = None,
) -> dict:
    return crud.latest_azure_image(db, arch)


@app.get("/versions")
def versions(db: Session = Depends(get_db)) -> list:  # noqa: B008
    return crud.find_available_versions(db)


@repeat(every(24).hours)
def self_update_image_data() -> None:
    """Update the database with new image data."""
    db = SessionLocal()
    wait_for_database(db)
    crud.update_image_data(db)


def run_schedule() -> None:
    """Background task to run the scheduled tasks."""
    run_all()
    while True:
        run_pending()
        sleep(1)


# Run the schedule in a separate thread
# NOTE(major): Pytest runs this code for some reason. This is a workaround.
if ENVIRONMENT != "testing":
    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.start()
