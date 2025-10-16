# SpotTheSpy Backend

A complete guide to set up, locally deploy and use <b>SpotTheSpy Backend</b> infrastructure

## System Requirements:

- Python 3.13+
- Poetry 1.8.3+
- Git
- Docker

## Development Instruments:

- [PyCharm](https://www.jetbrains.com/pycharm/)
- [pgAdmin](https://www.pgadmin.org/)
- [Redis Insight](https://redis.io/insight/)
- [Docker Desktop](https://docs.docker.com/desktop/)

## Setup

### Create a project with virtual environment

- Clone a repository to any directory using the command below:
```bash
git clone https://github.com/SpotTheSpy/backend.git
```
- Open the project with ```PyCharm```, but do not create a virtual environment.
- Activate a new ```Poetry``` environment and install dependencies by using the commands below:
```bash
poetry env activate
poetry install
```

### Prepare Environmental Variables

- Create ```.env``` file with this structure:
```
API_KEY={Any API-Key}

DATABASE_DSN=postgresql+psycopg://postgres:{Database Password}@localhost:5433/spotthespy

REDIS_DSN=redis://default:{Redis Password}@localhost:6379

S3_DSN=http://localhost:9000
S3_USERNAME=minio
S3_PASSWORD={MinIO Password}

RABBITMQ_DSN=amqp://rabbitmq:{RabbitMQ Password}@localhost:5672/

TELEGRAM_BOT_START_URL=https://t.me/{Bot Username}?start={payload}
```
Replace placeholders in curly brackets with any value (Except for payload, this should be in curly brackets for formatting), 
and if necessary, you can also add these optional variables:
```
TEST_DATABASE_DSN={Database DSN}  # Database for running tests
S3_REGION={AWS Region}  # Region of an AWS server
S3_REMOTE_DSN={S3 Remote DSN}  # DSN for generating direct URLs
RESULT_BACKEND_DSN={Result Backend DSN}  # DSN for celery task results retrieval

MIN_PLAYER_AMOUNT={Value}
MAX_PLAYER_AMOUNT={Value}
```
- Create ```.postgres.env``` with this structure:
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD={Database Password}
POSTGRES_DB=spotthespy
```
It must have the same credentials as a ```DATABASE_DSN``` variable.
- Create ```redis.conf``` with this structure:
```
requirepass {Redis Password}
```
Password must be the same as in ```REDIS_DSN``` variable.
- Create ```.minio.env``` with this structure:
```
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD={MinIO Password}
```
I think you got it now
- Create ```.rabbitmq.env``` with this structure:
```
RABBITMQ_DEFAULT_USER=rabbitmq
RABBITMQ_DEFAULT_PASS={RabbitMQ Password}
```

### Launch Docker Containers

To start all required Docker containers, simply run:
```bash
docker compose -f compose-local.yaml up -d
```

### Upgrade Migrations

To upgrade alembic migrations to head, run:
```bash
alembic upgrade head
```
If succeeded, then most likely your .env configuration and containers are set up correctly.

## Launch

### Start ASGI Server

To start an ASGI server, you can run either one of these commands:
```bash
python main.py
```
```bash
uvicorn --host 0.0.0.0 --port 8000 --loop asyncio --log-config app/logging.json app.asgi:app
```
Or just create a PyCharm run configuration of a ```main.py``` script.

### Start Celery Workers

Celery tasks are only required for specific features, sometimes development process may not require them.

To start a main Celery worker and a Celery beat, you need to run both of these commands in separate terminals:
```bash
celery -A app.workers.worker.worker worker --concurrency=1 --pool=solo --loglevel=INFO
```
```bash
celery -A app.workers.worker.worker beat --loglevel=INFO
```

## Usage

- Root API path provided by an ASGI server: http://localhost:8000/api
- API Swagger with each endpoint listed, documented and ready to use: http://localhost:8000/docs
- MinIO storage manager: http://localhost:9001
- RabbitMQ manager: http://localhost:5673

PostgreSQL's management via ```pgAdmin``` is accessible with these credentials:
- Username: ```postgres```
- Password: ```{Password in .postgres.env file}```
- Hostname: ```localhost```
- Port: ```5433```
- Database name: ```spotthespy```

Redis' management via ```Redis Insight``` is accessible with these credentials:
- Username: ```default```
- Password: ```{Password in redis.conf file}```
- Hostname: ```localhost```
- Port: ```6379```
