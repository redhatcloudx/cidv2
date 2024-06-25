# FastAPI Docs: https://fastapi.tiangolo.com/deployment/docker/#docker-image-with-poetry
FROM python:3.12 as requirements-stage
WORKDIR /tmp
RUN pip install poetry poetry-plugin-export
COPY ./pyproject.toml ./poetry.lock* /tmp/
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.12
WORKDIR /code
COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./cid /code/cid

CMD ["uvicorn", "--host", "0.0.0.0", "cid.main:app"]
