from abc import ABC
from typing import ClassVar, TYPE_CHECKING, Any, Dict, Optional, Self

from app.assets.objects.abstract import AbstractObject

if TYPE_CHECKING:
    from app.assets.controllers.redis import RedisController
else:
    RedisController = Any


class AbstractRedisObject(AbstractObject, ABC):
    """
    Abstract class for Redis objects.

    This is an abstract class for objects which represent specific values in a Redis database.

    Redis key is usually constructed from a default redis key from a controller instance,
    a key class argument unique for every redis object class,
    and a primary key which must be unique for every redis object.

    Value is a JSON-Serialized object by to_json() method.
    """

    key: ClassVar[str]
    """
    Unique object class key.
    """

    _controller: Optional['RedisController'] = None
    """
    Redis controller instance.
    """

    @property
    def controller(self) -> 'RedisController':
        """
        Redis controller instance. A private parameter must be set after an object initialization.

        :raise ValueError: If a controller instance is not set.
        :return: Redis controller instance.
        """
        if self._controller is None:
            raise ValueError("Controller is not set")
        return self._controller

    @classmethod
    def from_json_and_controller(
            cls,
            data: Dict[str, Any],
            *,
            controller: 'RedisController',
            **kwargs: Any
    ) -> Self | None:
        """
        Reconstruct an object instance from a JSON-Serialized dictionary and a controller instance.

        :param data: Dictionary to reconstruct an object instance.
        :param controller: Redis controller instance.
        :param kwargs: Any additional JSON-Serializable parameters.
        :return: An object instance if validated successfully, else None.
        """

        value = cls.from_json(data, **kwargs)

        if value is not None:
            value._controller = controller

        return value

    async def save(self, *, expire: int | None = None) -> None:
        """
        Save an object to Redis.

        :param expire: Expiration time in seconds.
        """

        await self.controller.set(self, expire=expire)

    async def clear(self) -> None:
        """
        Clear an object from Redis.
        """

        await self.controller.remove(self.primary_key)
