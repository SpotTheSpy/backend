from abc import ABC
from typing import ClassVar, TYPE_CHECKING, Any

from pydantic.dataclasses import dataclass

from app.assets.objects.abstract import AbstractObject

if TYPE_CHECKING:
    from app.assets.controllers.redis import RedisController
else:
    AbstractRedisController = Any


@dataclass
class AbstractRedisObject(AbstractObject, ABC):
    key: ClassVar[str]

    _controller: 'RedisController'

    @property
    def controller(self) -> 'RedisController':
        return self._controller

    async def save(self) -> None:
        await self.controller.set(self)

    async def clear(self) -> None:
        await self.controller.remove(self.primary_key)
