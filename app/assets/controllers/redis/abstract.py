import json
from abc import ABC, abstractmethod
from typing import Any, Tuple, List

from redis.asyncio import Redis


class RedisController(ABC):
    def __init__(
            self,
            redis: Redis
    ) -> None:
        self._redis: Redis = redis

    @abstractmethod
    def key(self, *args, **kwargs) -> str: pass

    async def set(
            self,
            key: str,
            value: Any,
            *,
            exact_key: bool = False
    ) -> None:
        await self._redis.set(key if exact_key else f"spotthespy:{key}", json.dumps(value))

    async def get(
            self,
            key: str,
            *,
            exact_key: bool = False
    ) -> Any:
        serialized: str = await self._redis.get(key if exact_key else f"spotthespy:{key}")
        return json.loads(serialized) if serialized is not None else None

    async def get_keys(
            self,
            *,
            pattern: str = "",
            exact_pattern: bool = False
    ) -> Tuple[str, ...]:
        keys: List[bytes] = await self._redis.keys(f"*{pattern}*" if exact_pattern else f"*spotthespy:{pattern}*")
        return tuple([key.decode() for key in keys])

    async def exists(
            self,
            key: str,
            *,
            exact_key: bool = False
    ) -> bool:
        return bool(await self._redis.exists(key if exact_key else f"spotthespy:{key}"))

    async def remove(
            self,
            key: str,
            *,
            exact_key: bool = False
    ) -> None:
        await self._redis.delete(key if exact_key else f"spotthespy:{key}")
