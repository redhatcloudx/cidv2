FROM python:3.12
# Ensure poetry does not create a virtualenv
ENV POETRY_VIRTUALENVS_CREATE=false

RUN pip install poetry
WORKDIR /code
COPY poetry.lock pyproject.toml /code/
RUN poetry install --no-interaction --no-ansi --no-root --no-dev

COPY cid /code/cid/
COPY import_data.py /code/
COPY README.md /code/
CMD ["poetry", "run", "uvicorn", "cid.main:app", "--host 0.0.0.0", "--port 80"]
