#!/bin/sh

echo "Loading data from S3..."
curl -sLo ./data.json https://cloudx-json-bucket.s3.amazonaws.com/raw/aws/aws.json

# Keep trying to load data if the database is still initializing.
until poetry run python ./import_data.py aws
do
    echo "Import failed, retrying in 5 seconds..."
    sleep 5
done

poetry run uvicorn cid.main:app --host 0.0.0.0 --port 80
