from logging import getLogger
from os import getenv
from sys import exit
from typing import Generator, Optional

from fastapi import Depends, FastAPI
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from cid import crud
from cid.database import SessionLocal
from cid.models import AwsImage

log = getLogger(__name__)

# Pack the database into the container build and then exit immediately.
if getenv("POPULATE_DB_ONLY", "0") == "1":
    log.info("Only populating the database.")

    db = SessionLocal()
    crud.update_image_data(db)

    log.info("Database population complete. Exiting.")
    exit(0)

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


@app.get("/aws")
def all_aws_images(db: Session = Depends(get_db)) -> list:  # noqa: B008
    result = db.query(AwsImage).order_by(AwsImage.creationDate.desc()).all()
    return list(jsonable_encoder(result))


@app.get("/aws/latest")
def latest_aws_image(db: Session = Depends(get_db), arch: Optional[str] = None) -> dict:  # noqa: B008
    return crud.latest_aws_image(db, arch)


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
