#!/bin/sh

curl -o ./data.json https://cloudx-json-bucket.s3.amazonaws.com/raw/aws/aws.json
poetry install
poetry run python ./import_data.py aws
poetry run uvicorn cid.main:app --host 0.0.0.0 --port 80
