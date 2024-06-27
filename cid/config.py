"""Centralized configuration for the project."""

import os

# Get the current environment (default to testing if not set).
ENVIRONMENT = os.getenv("ENVIRONMENT", "testing")

# Database connection string.
DATABASE_URLS = {
    # NOTE(mhayden): The four slashes in the production database path ensures
    # that an absolute path is used.
    "production": "sqlite:////cid.db",
    # In-memory databases are much faster for testing.
    "testing": "sqlite:///:memory:",
}
DATABASE_URL = DATABASE_URLS[ENVIRONMENT]

# Image data for populating the database.
IMAGE_DATA_BASE_URL = "https://cloudx-json-bucket.s3.amazonaws.com/raw"
AWS_IMAGE_DATA = f"{IMAGE_DATA_BASE_URL}/aws/aws.json"
AZURE_IMAGE_DATA = f"{IMAGE_DATA_BASE_URL}/azure/eastus.json"
GOOGLE_IMAGE_DATA = f"{IMAGE_DATA_BASE_URL}/google/global.json"

# Supported cloud providers.
CLOUD_PROVIDERS = ["aws", "azure", "google"]
