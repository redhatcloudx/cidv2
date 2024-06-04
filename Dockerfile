FROM python:3.12

WORKDIR /app

COPY pyproject.toml .
RUN pip install poetry && poetry install
RUN pip install fastapi uvicorn

COPY . .
RUN chmod +x ./entrypoint.sh