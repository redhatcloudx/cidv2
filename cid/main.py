import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from cid.config import DATABASE_URL
from cid.models import AwsImage, AzureImage, GoogleImage

log = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app = FastAPI()


@app.get("/")
def read_root() -> dict:
    return {"Hello": "World"}


def latest_aws_image(request: Request) -> Dict[str, Any]:
    db = SessionLocal()
    regions = db.query(AwsImage.region).distinct().order_by(AwsImage.region).all()
    latest_image = (
        db.query(AwsImage).order_by(desc(AwsImage.version), desc(AwsImage.date)).first()
    )

    if latest_image is None:
        return {"error": "No images found", "code": 404}

    images = {}
    for region in regions:
        region_image = (
            db.query(AwsImage)
            .filter(AwsImage.region == region[0], AwsImage.name == latest_image.name)
            .first()
        )
        if region_image is not None:
            images[region[0]] = region_image.imageId

    return {
        "name": latest_image.name,
        "version": latest_image.version,
        "date": latest_image.date,
        "amis": images,
    }


def latest_azure_image(request: Request) -> Dict[str, Any]:
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


def latest_google_image(request: Request) -> Dict[str, Any]:
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
def latest(request: Request) -> Dict[str, Any]:
    return {
        "latest_aws_image": latest_aws_image(request),
        "latest_azure_image": latest_azure_image(request),
        "latest_google_image": latest_google_image(request),
    }
