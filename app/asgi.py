import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import ValidationError
from redis.asyncio import Redis
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.router import api_router
from app.api.v1.exceptions.http import HTTPError
from app.assets.controllers.redis.redis import RedisController
from app.assets.controllers.redis.secret_words import SecretWordsController
from app.assets.controllers.s3.abstract import S3Config
from app.assets.controllers.s3.qr_codes import QRCodesController
from app.assets.objects.multi_device_active_player import MultiDeviceActivePlayer
from app.assets.objects.multi_device_game import MultiDeviceGame
from app.assets.objects.single_device_active_player import SingleDeviceActivePlayer
from app.assets.objects.single_device_game import SingleDeviceGame
from app.database.database import Database
from app.logging import logger
from config import Config


def get_blurred_qr_code() -> bytes:
    with open("app/assets/data/blurred.jpg", "rb") as file:
        return file.read()


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    blurred_qr_code: bytes = await asyncio.to_thread(get_blurred_qr_code)
    await fastapi_app.state.qr_codes.add("blurred.jpg", blurred_qr_code)

    yield

    await fastapi_app.state.redis.close()


config = Config(_env_file=".env")
database = Database.from_dsn(config.database_dsn.get_secret_value())
redis = Redis.from_url(config.redis_dsn.get_secret_value())
s3_config = S3Config(
    config.s3_dsn.get_secret_value(),
    config.s3_region,
    config.s3_username.get_secret_value(),
    config.s3_password.get_secret_value()
)

app = FastAPI(title=config.title, lifespan=lifespan)

app.state.config = config
app.state.database = database
app.state.redis = redis
app.state.secret_words = SecretWordsController(redis)
app.state.single_device_games = RedisController[SingleDeviceGame](redis)
app.state.single_device_players = RedisController[SingleDeviceActivePlayer](redis)
app.state.multi_device_games = RedisController[MultiDeviceGame](redis)
app.state.multi_device_players = RedisController[MultiDeviceActivePlayer](redis)
app.state.qr_codes = QRCodesController(s3_config)

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
