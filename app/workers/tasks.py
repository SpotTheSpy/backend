import asyncio
import json
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError

from app.workers.worker import worker, config


async def __async_save_to_redis(key: str, value: Any) -> None:
    redis = Redis.from_url(config.redis_dsn.get_secret_value())
    await redis.set(f"spotthespy:{key}", json.dumps(value))


async def __async_clear_from_redis(key: str) -> None:
    redis = Redis.from_url(config.redis_dsn.get_secret_value())
    await redis.delete(f"spotthespy:{key}")


@worker.task(autoretry_for=(ConnectionError, TimeoutError), retry_backoff=True, max_retries=3)
def save_to_redis(key: str, value: Any) -> None:
    asyncio.run(__async_save_to_redis(key, value))


@worker.task(autoretry_for=(ConnectionError, TimeoutError), retry_backoff=True, max_retries=3)
def clear_from_redis(key: str) -> None:
    asyncio.run(__async_clear_from_redis(key))
