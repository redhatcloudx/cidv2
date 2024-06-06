"""Database models."""

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Avoid ruff getting upset about the id column below.
# ruff: noqa: A003


class AwsImage(Base):
    __tablename__ = "aws_images"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    arch = Column(String)
    version = Column(String)
    imageId = Column(String)
    date = Column(DateTime)
    virt = Column(String)
    provider = Column(String)
    region = Column(String)
    imageLocation = Column(String)
    imageType = Column(String)
    public = Column(Boolean)
    ownerId = Column(String)
    platformDetails = Column(String)
    usageOperation = Column(String)
    state = Column(String)
    blockDeviceMappings = Column(JSON)
    description = Column(String)
    enaSupport = Column(Boolean)
    hypervisor = Column(String)
    rootDeviceName = Column(String)
    rootDeviceType = Column(String)
    sriovNetSupport = Column(String)
    deprecationTime = Column(DateTime)
