from fastapi import FastAPI
from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker
from app.models import Image

DATABASE_URL = 'postgresql://postgres:postgres@db:5432/test_db'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/latest")
def get_latest_image():
    db = SessionLocal()
    latest_image = db.query(Image).order_by(desc(Image.version), desc(Image.date)).first()
    return {"latest_image": latest_image.name}
