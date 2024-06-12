import logging
from typing import Any, Dict, Generator

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from cid import crud
from cid.database import SessionLocal

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
