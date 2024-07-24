FROM registry.access.redhat.com/ubi9/python-312
LABEL "com.redhat.component" = "cid-cloudx"
LABEL "description" = "Cloud Image Directory API"
LABEL "io.k8s.description" = "Cloud Image Directory API"
LABEL "io.k8s.display-name" = "cid-api"
LABEL "io.openshift.tags" = "cid,api"
LABEL "name" = "cid-api"
LABEL "summary" = "A dynamic API endpoint to serve RHEL cloud image data."

USER 1001

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/opt/app-root/src/.local/bin:$PATH"

WORKDIR /code
COPY --chown=1001:0 poetry.lock pyproject.toml /code/
COPY --chown=1001:0 cid /code/cid/
COPY --chown=1001:0 import_data.py /code/
COPY --chown=1001:0 README.md /code/

RUN poetry env use python3.12
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-root --only=main

RUN env ENVIRONMENT=production poetry run populatedb
CMD ["poetry", "run", "uvicorn", "--host", "0.0.0.0", "--port", "8080", "cid.main:app"]
