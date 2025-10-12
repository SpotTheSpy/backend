# Using Python slim image 3.13
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim
ENV POETRY_VIRTUALENVS_IN_PROJECT=1

# Preparing image
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Copying project requirements files to workdir and installing dependencies
WORKDIR /opt/app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --only main --no-interaction

# Copying the entire project
COPY . .

# Setting container user
RUN adduser --disabled-password appuser && chown -R appuser .
USER appuser
