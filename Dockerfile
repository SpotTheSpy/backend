ARG PYTHON_VERSION=3.13
ARG POETRY_VERSION=1.8.3

FROM python:${PYTHON_VERSION}-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry==${POETRY_VERSION} && poetry install

COPY . .

RUN adduser useradd -m --disable-password appuser && chown -R appuser .
USER appuser

ENTRYPOINT ["poetry", "run"]
