ARG PYTHON_VERSION=3.13

FROM python:${PYTHON_VERSION}-slim

ENV POETRY_VIRTUALENVS_IN_PROJECT=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install

COPY . .

RUN adduser --disabled-password appuser && chown -R appuser .
USER appuser
