import logging
from typing import Any, Dict, Generator

from fastapi import Depends, FastAPI
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import Session, sessionmaker

from cid import crud
from cid.config import DATABASE_URL
from cid.models import AzureImage, GoogleImage

log = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
    db = SessionLocal()
    latest_image = db.query(AzureImage).order_by(desc(AzureImage.version)).first()

    if latest_image is None:
        return {"error": "No images found", "code": 404}

    return {
        "sku": latest_image.sku,
        "offer": latest_image.offer,
        "version": latest_image.version,
        "urn": latest_image.urn,
    }


def latest_google_image(db: Session) -> Dict[str, Any]:
    db = SessionLocal()
    latest_image = (
        db.query(GoogleImage)
        .order_by(desc(GoogleImage.version), desc(GoogleImage.creationTimestamp))
        .first()
    )

    if latest_image is None:
        return {"error": "No images found", "code": 404}

    return {
        "name": latest_image.name,
        "version": latest_image.version,
        "date": latest_image.creationTimestamp,
        "selfLink": latest_image.selfLink,
    }


@app.get("/latest")
def latest(db: Session = Depends(get_db)) -> Dict[str, Any]:  # noqa: B008
    return {
        "latest_aws_image": latest_aws_image(db),
        "latest_azure_image": latest_azure_image(db),
        "latest_google_image": latest_google_image(db),
    }
