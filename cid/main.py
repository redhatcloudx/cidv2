from typing import Any, Dict

from fastapi import FastAPI, Request
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from cid.config import DATABASE_URL
from cid.models import AwsImage

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app = FastAPI()


@app.get("/")
def read_root() -> dict:
    return {"Hello": "World"}


@app.get("/latest")
def latest(request: Request) -> Dict[str, Any]:
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
        "latest_aws_image": {
            "name": latest_image.name,
            "version": latest_image.version,
            "date": latest_image.date,
            "images": images,
        }
    }
