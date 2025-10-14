from contextlib import asynccontextmanager
from typing import AsyncContextManager

from fastapi import FastAPI
from pydantic import ValidationError
from redis.asyncio import Redis
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.router import api_router
from app.api.v1.exceptions.http import HTTPError
from app.assets.controllers.redis import RedisController
from app.assets.controllers.s3 import S3Config, S3Controller
from app.assets.objects.multi_device_active_player import MultiDeviceActivePlayer
from app.assets.objects.multi_device_game import MultiDeviceGame
from app.assets.objects.qr_code import QRCode
from app.assets.objects.secret_words_queue import SecretWordsQueue
from app.assets.objects.single_device_active_player import SingleDeviceActivePlayer
from app.assets.objects.single_device_game import SingleDeviceGame
from app.database.database import Database
from app.logging import logger
from config import Config


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncContextManager[None]:
    """
    FastAPI app lifespan.

    Defines startup and shutdown logic.

    :param fastapi_app: FastAPI app to provide lifespan for.
    """

    yield
    await fastapi_app.state.redis.close()


config = Config(_env_file=".env")
database = Database.from_dsn(config.database_dsn.get_secret_value())
redis = Redis.from_url(config.redis_dsn.get_secret_value())
s3_config = S3Config.from_config(config)

app = FastAPI(title=config.TITLE, lifespan=lifespan)

app.state.config = config
app.state.database = database
app.state.redis = redis

app.state.secret_words = RedisController[SecretWordsQueue](redis)
app.state.single_device_games = RedisController[SingleDeviceGame](redis)
app.state.single_device_players = RedisController[SingleDeviceActivePlayer](redis)
app.state.multi_device_games = RedisController[MultiDeviceGame](redis)
app.state.multi_device_players = RedisController[MultiDeviceActivePlayer](redis)

app.state.qr_codes = S3Controller[QRCode](s3_config)

app.include_router(api_router)


@app.exception_handler(ValidationError)
async def on_validation_error(
        request: Request,
        exception: ValidationError
) -> JSONResponse:
    """
    Handler for Pydantic validation errors.

    Executes when a Pydantic model provided by either user or ASGI is invalid.

    :param request: API request instance.
    :param exception: ValidationError instance.
    :return: JSON API response.
    """

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exception.errors()}
    )


@app.exception_handler(HTTPError)
async def on_http_error(
        request: Request,
        exception: HTTPError
) -> JSONResponse:
    """
    Handler for HTTP errors.

    Executes when ASGI server raises a business-logic level exception,
    such as invalid access credentials or object not found.

    :param request: API request instance.
    :param exception: HTTPError instance.
    :return: JSON API response.
    """

    return JSONResponse(
        status_code=exception.status_code,
        content={"detail": str(exception)}
    )


@app.exception_handler(Exception)
async def on_server_error(
        request: Request,
        exception: Exception
) -> JSONResponse:
    """
    Handler for all errors.

    Executes when ASGI server raises any internal exception which should be inspected and debugged.

    :param request: API request instance.
    :param exception: Exception instance.
    :return: JSON API response.
    """

    logger.exception(exception)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
