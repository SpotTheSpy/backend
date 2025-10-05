from typing import AsyncGenerator

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.assets.controllers.redis.secret_words import SecretWordsController
from app.assets.controllers.redis.single_device_games import SingleDeviceGamesController
from app.assets.controllers.s3.qr_codes import QRCodesController
from app.assets.objects.multi_device_game import MultiDeviceGamesController
from app.database.database import Database
from config import Config


async def config_dependency(request: Request) -> Config:
    return request.app.state.config


async def database_dependency(request: Request) -> Database:
    return request.app.state.database


async def database_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with request.app.state.database.session_maker() as session:
        yield session


async def redis_dependency(request: Request) -> Redis:
    return request.app.state.redis


async def secret_words_dependency(request: Request) -> SecretWordsController:
    return request.app.state.secret_words


async def single_device_games_dependency(request: Request) -> SingleDeviceGamesController:
    return request.app.state.single_device_games


async def multi_device_games_dependency(request: Request) -> MultiDeviceGamesController:
    return request.app.state.multi_device_games


async def qr_codes_dependency(request: Request) -> QRCodesController:
    return request.app.state.qr_codes
