from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from app.api.router import api_router
from app.database.database import Database
from config import Config


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    yield
    await fastapi_app.state.redis.close()


app = FastAPI()

config = Config(_env_file=".env")
database = Database.from_dsn(config.database_dsn.get_secret_value())
redis = Redis.from_url(config.redis_dsn.get_secret_value())

app.state.config = config
app.state.database = database
app.state.redis = redis

app.include_router(api_router)
