"""Shared items for testing."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from cid.models import AwsImage, AzureImage


@pytest.fixture(scope="function")
def db_engine(request):
    """yields a SQLAlchemy engine which is suppressed after the test session"""
    engine_ = create_engine("sqlite:///:memory:")

    # Add tables to the database.
    AwsImage.metadata.create_all(bind=engine_)
    AzureImage.metadata.create_all(bind=engine_)

    yield engine_

    # Remove tables.
    AwsImage.metadata.drop_all(bind=engine_)
    AzureImage.metadata.create_all(bind=engine_)

    engine_.dispose()


@pytest.fixture(scope="function")
def db_session_factory(db_engine):
    """returns a SQLAlchemy scoped session factory"""
    return scoped_session(sessionmaker(bind=db_engine))


@pytest.fixture(scope="function")
def db_session(db_session_factory):
    """yields a SQLAlchemy connection which is rollbacked after the test"""
    session_ = db_session_factory()

    yield session_

    session_.rollback()
    session_.close()
