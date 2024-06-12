"""Shared items for testing."""

import pytest

from cid.database import SessionLocal, engine
from cid.models import AwsImage, AzureImage, GoogleImage


@pytest.fixture(scope="function")
def db():
    """Yield a sqlalchemy database connection after creating the tables."""
    db = SessionLocal()

    AwsImage.metadata.create_all(bind=engine)
    AzureImage.metadata.create_all(bind=engine)
    GoogleImage.metadata.create_all(bind=engine)

    yield db

    AwsImage.metadata.drop_all(bind=engine)
    AzureImage.metadata.drop_all(bind=engine)
    GoogleImage.metadata.drop_all(bind=engine)

    db.rollback()
    db.close()
