import logging
from typing import Any, Dict, Generator

from fastapi import Depends, FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from cid import crud
from cid.config import DATABASE_URL

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
