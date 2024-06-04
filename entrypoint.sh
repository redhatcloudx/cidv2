#!/bin/sh

curl -o ./data.json https://imagedirectory.cloud/images/v2/all
poetry install
poetry run python ./import_data.py
poetry run uvicorn app.main:app --host 0.0.0.0 --port 80