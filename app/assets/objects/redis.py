from abc import ABC
from typing import ClassVar, TYPE_CHECKING, Any, Dict, Optional

from pydantic import ValidationError

from app.assets.objects.abstract import AbstractObject

if TYPE_CHECKING:
    from app.assets.controllers.redis import RedisController
else:
    AbstractRedisController = Any


class AbstractRedisObject(AbstractObject, ABC):
    key: ClassVar[str]

    _controller: Optional['RedisController']

    @property
    def controller(self) -> 'RedisController':
        if self._controller is None:
            raise ValueError("Controller is not set")
        return self._controller

    @classmethod
    def from_json_and_controller(
            cls,
            data: Dict[str, Any],
            *,
            controller: 'RedisController'
    ) -> Optional['AbstractRedisObject']:
        try:
            value = cls.model_validate(data)
            value._controller = controller

            return value
        except ValidationError:
            pass

    async def save(self) -> None:
        await self.controller.set(self)

    async def clear(self) -> None:
        await self.controller.remove(self.primary_key)
