from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import ValidationError
from redis.asyncio import Redis
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.router import api_router
from app.api.v1.exceptions.http import HTTPError
from app.assets.controllers.redis.locales import LocalesController
from app.assets.controllers.redis.single_device_games import SingleDeviceGamesController
from app.database.database import Database
from app.logging import logger
from config import Config


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    yield
    await fastapi_app.state.redis.close()


config = Config(_env_file=".env")
database = Database.from_dsn(config.database_dsn.get_secret_value())
redis = Redis.from_url(config.redis_dsn.get_secret_value())

app = FastAPI(title=config.title, lifespan=lifespan)

app.state.config = config
app.state.database = database
app.state.redis = redis
app.state.locales = LocalesController(redis)
app.state.single_games = SingleDeviceGamesController(redis)

app.include_router(api_router)


@app.exception_handler(ValidationError)
async def on_validation_error(request: Request, exception: ValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exception.errors()}
    )


@app.exception_handler(HTTPError)
async def on_http_error(request: Request, exception: HTTPError) -> JSONResponse:
    return JSONResponse(
        status_code=exception.status_code,
        content={"detail": str(exception)}
    )


@app.exception_handler(Exception)
async def on_server_error(
        request: Request,
        exception: Exception
) -> JSONResponse:
    logger.exception(exception)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"}
    )
