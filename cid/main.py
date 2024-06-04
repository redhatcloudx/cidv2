from fastapi import FastAPI
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from cid.models import Image

DATABASE_URL = "postgresql://postgres:postgres@db:5432/test_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app = FastAPI()


@app.get("/")
def read_root() -> dict:
    return {"Hello": "World"}


@app.get("/latest")
def get_latest_image() -> dict:
    db = SessionLocal()
    latest_image = (
        db.query(Image).order_by(desc(Image.version), desc(Image.date)).first()
    )
    if latest_image is None:
        return {"latest_image": None}

    return {"latest_image": latest_image.name}
