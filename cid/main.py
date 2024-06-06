from fastapi import FastAPI
from sqlalchemy import create_engine, desc, func, and_
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
    providers = db.query(Image.provider).distinct().all()

    result = {}
    for provider in providers:
        if provider[0] == "aws":
            result["aws"] = {}
            regions = (
              db.query(Image.region)
              .filter(Image.provider == "aws")
              .distinct()
              .all()
            )
            latest_image = (
                db.query(Image)
                .filter(Image.provider == "aws")
                .order_by(desc(Image.version), desc(Image.date))
                .first()
            )
            result["aws"][latest_image.name] = {}
            for region in regions:
                image = (
                  db.query(Image)
                  .filter(and_(
                    Image.provider == "aws",
                    Image.region == region[0],
                    Image.name == latest_image.name
                  ))
                  .first()
                )
                if image:
                  result["aws"][image.name][region[0]] = image.imageId
        else:
            result[provider[0]] = {}
            image = (
                db.query(Image)
                .filter(Image.provider == provider[0])
                .order_by(Image.version.desc(), Image.date.desc())
                .first()
            )
            if image:
                result[provider[0]][image.name] = {}
                result[provider[0]][image.name] = image.imageId

    return {"latest_image_up": result}
