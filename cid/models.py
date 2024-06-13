"""Database models."""

from sqlalchemy import JSON, Column, DateTime, Integer, String

from cid.database import Base

# Avoid ruff getting upset about the id column below.
# ruff: noqa: A003


class AwsImage(Base):
    __tablename__ = "aws_images"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    arch = Column(String)
    version = Column(String)
    imageId = Column(String)
    date = Column(DateTime)
    provider = Column(String)
    region = Column(String)
    description = Column(String)
    deprecationTime = Column(DateTime)


class GoogleImage(Base):
    __tablename__ = "google_images"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    arch = Column(String)
    version = Column(String)
    creationTimestamp = Column(DateTime)
    description = Column(String)
    diskSizeGb = Column(Integer)
    family = Column(String)
    guestOsFeatures = Column(JSON)
    kind = Column(String)
    labelFingerprint = Column(String)
    licenseCodes = Column(JSON)
    licenses = Column(JSON)
    rawDisk = Column(JSON)
    selfLink = Column(String)
    sourceType = Column(String)
    status = Column(String)
    storageLocations = Column(JSON)


class AzureImage(Base):
    __tablename__ = "azure_images"

    id = Column(String, primary_key=True, index=True)
    architecture = Column(String)
    offer = Column(String)
    publisher = Column(String)
    sku = Column(String)
    urn = Column(String)
    version = Column(String)
