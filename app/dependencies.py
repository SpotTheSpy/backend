from typing import AsyncGenerator

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.assets.controllers.redis.locales import LocalesController
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


async def locales_dependency(request: Request) -> LocalesController:
    return request.app.state.locales
