"""Centralized configuration for the project."""

# Postgres database connection string.
DATABASE_URL = "postgresql://postgres:postgres@db:5432/test_db"

# Image data for populating the database.
IMAGE_DATA_BASE_URL = "https://cloudx-json-bucket.s3.amazonaws.com/raw"
AWS_IMAGE_DATA = f"{IMAGE_DATA_BASE_URL}/aws/aws.json"
AZURE_IMAGE_DATA = f"{IMAGE_DATA_BASE_URL}/azure/eastus.json"
GCP_IMAGE_DATA = f"{IMAGE_DATA_BASE_URL}/google/global.json"
