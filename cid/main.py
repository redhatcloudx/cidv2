import logging
import threading
from time import sleep
from typing import Any, Dict, Generator

from fastapi import Depends, FastAPI
from schedule import every, repeat, run_all, run_pending
from sqlalchemy.orm import Session

from cid import crud
from cid.database import SessionLocal
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


def latest_aws_image(db: Session) -> Dict[str, Any]:
    return crud.latest_aws_image(db)


def latest_azure_image(db: Session) -> Dict[str, Any]:
    return crud.latest_azure_image(db)


def latest_google_image(db: Session) -> Dict[str, Any]:
    return crud.latest_google_image(db)


@app.get("/latest")
def latest(db: Session = Depends(get_db)) -> Dict[str, Any]:  # noqa: B008
    return {
        "latest_aws_image": latest_aws_image(db),
        "latest_azure_image": latest_azure_image(db),
        "latest_google_image": latest_google_image(db),
    }


@repeat(every(10).minutes)
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
schedule_thread = threading.Thread(target=run_schedule)
schedule_thread.start()
