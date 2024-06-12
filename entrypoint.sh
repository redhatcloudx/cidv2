#!/bin/sh
poetry run uvicorn cid.main:app --host 0.0.0.0 --port 80
