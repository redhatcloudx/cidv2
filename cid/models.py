"""Database models."""

from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Avoid ruff getting upset about the id column below.
# ruff: noqa: A003


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    arch = Column(String)
    version = Column(String)
    imageId = Column(String)
    date = Column(Date)
    virt = Column(String)
    provider = Column(String)
    region = Column(String)
