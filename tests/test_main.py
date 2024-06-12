"""Tests for the main module."""

from datetime import datetime

from fastapi.testclient import TestClient

from cid.database import SessionLocal, engine
from cid.main import app, latest_aws_image
from cid.models import AwsImage

# Create a TestClient instance to test the FastAPI app
# https://fastapi.tiangolo.com/tutorial/testing/
client = TestClient(app)


def test_read_root():
    """Test the read_root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


def test_latest_aws_image():
    AwsImage.metadata.create_all(bind=engine)

    db = SessionLocal()
    aws_image = AwsImage(
        id="ami-12345678",
        name="test_image",
        version="1.0",
        # SQLite only supports datetime objects
        date=datetime.strptime("2022-01-01", "%Y-%m-%d").date(),
        region="us-west-1",
        imageId="ami-12345678",
    )
    db.add(aws_image)
    db.commit()

    response = latest_aws_image(db)

    assert response == {
        "name": "test_image",
        "version": "1.0",
        "date": datetime(2022, 1, 1, 0, 0),
        "amis": {"us-west-1": "ami-12345678"},
    }
