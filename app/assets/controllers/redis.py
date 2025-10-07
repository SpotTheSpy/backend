from functools import partial
from inspect import FullArgSpec, getfullargspec
from json import dumps, loads
from typing import Any, Tuple, List, TypeVar, Callable, Dict, Generic

from redis.asyncio import Redis

from app.assets.controllers.abstract import AbstractController
from app.assets.objects.redis import AbstractRedisObject
from app.assets.parameters import Parameters

T = TypeVar('T', bound=AbstractRedisObject)


class RedisController(Generic[T], AbstractController):
    def __init__(
            self,
            redis: Redis,
            *,
            default_key: str | None = None
    ) -> None:
        self._redis: Redis = redis
        self._default_key: str = default_key or Parameters.DEFAULT_REDIS_KEY

    @property
    def key(self) -> str:
        try:
            return self.object_class.key
        except NameError:
            raise ValueError("Key attribute in generic redis object class is not set")

    async def set(
            self,
            value: T
    ) -> None:
        await self._set(str(value.primary_key), value.to_json())

    async def get(
            self,
            primary_key: Any,
            from_json_method: Callable[..., T] | None = None,
            **kwargs: Any
    ) -> T | None:
        value: Dict[str, Any] | None = await self._get(str(primary_key))

        if from_json_method is None:
            from_json_method = self.object_class.from_json_and_controller

        return None if value is None else from_json_method(
            value,
            controller=self,
            **kwargs
        )

    async def exists(
            self,
            primary_key: Any
    ) -> bool:
        return await self._exists(str(primary_key))

    async def remove(
            self,
            primary_key: Any
    ) -> None:
        await self._remove(str(primary_key))

    async def all(
            self,
            *,
            limit: int | None = None,
            offset: int | None = None,
            count: int | None = None,
            from_json_method: Callable[..., T] | None = None,
            **kwargs: Any
    ) -> Tuple[T, ...]:
        values: List[T] = []

        if from_json_method is None:
            from_json_method = self.object_class.from_json_and_controller

        for key in await self._get_keys(limit=limit, offset=offset, count=count):
            value = from_json_method(
                await self._get(key, exact_key=True),
                controller=self,
                **kwargs
            )

            if value is None:
                continue

            values.append(value)

        return tuple(values)

    def _key(self, *args: str, exact: bool = False) -> str:
        keys: Tuple[str, ...] = (*args,) if exact else (self._default_key, self.key, *args)
        return ":".join(keys)

    def _pattern(self, *, exact: bool = False) -> str:
        return "" if exact else f"*{self._default_key}:{self.key}*"

    async def _set(self, key: str, value: Any, *, exact_key: bool = False) -> None:
        await self._redis.set(self._key(key, exact=exact_key), dumps(value))

    async def _get(self, key: str, *, exact_key: bool = False) -> Any:
        serialized: str = await self._redis.get(self._key(key, exact=exact_key))
        return loads(serialized) if serialized is not None else None

    async def _exists(self, key: str, *, exact_key: bool = False) -> bool:
        return bool(await self._redis.exists(self._key(key, exact=exact_key)))

    async def _remove(self, key: str, *, exact_key: bool = False) -> None:
        await self._redis.delete(self._key(key, exact=exact_key))

    async def _get_keys(
            self,
            *,
            pattern: str | None = None,
            limit: int | None = None,
            offset: int | None = None,
            count: int | None = None
    ) -> Tuple[str, ...]:
        if limit is None:
            limit = 100
        if offset is None:
            offset = 0
        if count is None:
            count = 100

        cursor: int = 0
        skipped: int = 0
        collected: List[str] = []

        while True:
            cursor, keys = await self._redis.scan(
                cursor=cursor,
                match=f"*{pattern}*" if pattern is not None else self._pattern(),
                count=count
            )

            for key in keys:
                if skipped < offset:
                    skipped += 1
                    continue
                if len(collected) < limit:
                    collected.append(key.decode())
                if len(collected) >= limit:
                    return tuple(collected)

            if cursor == 0:
                break

        return tuple(collected)

    @staticmethod
    def _prepare_function(
            function: Callable[..., Callable],
            **kwargs: Any
    ) -> partial:
        arg_spec: FullArgSpec = getfullargspec(function)

        args: List[str] = arg_spec.args + arg_spec.kwonlyargs

        if arg_spec.varkw is None:
            kwargs = {
                k: arg for k, arg in kwargs.items()
                if k in args
            }

        return partial(function, **kwargs)
