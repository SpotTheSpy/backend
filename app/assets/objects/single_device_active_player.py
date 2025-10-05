from typing import Any, Dict, TYPE_CHECKING
from uuid import UUID

from pydantic.dataclasses import dataclass

from app.assets.objects.redis import RedisObject

if TYPE_CHECKING:
    from app.assets.controllers.redis.single_device_games import SingleDeviceGamesController
else:
    SingleDeviceGamesController = Any


@dataclass
class SingleDeviceActivePlayer(RedisObject):
    game_id: UUID
    user_id: UUID

    _controller: 'SingleDeviceGamesController'

    @classmethod
    def new(
            cls,
            game_id: UUID,
            user_id: UUID,
            *,
            controller: 'SingleDeviceGamesController',
    ) -> 'SingleDeviceActivePlayer':
        return cls(
            game_id=game_id,
            user_id=user_id,
            _controller=controller
        )

    @classmethod
    def from_json(
            cls,
            data: Dict[str, Any],
            *,
            controller: 'SingleDeviceGamesController'
    ) -> Any:
        return cls(**data, _controller=controller)

    def to_json(self) -> Dict[str, Any]:
        return {
            "game_id": str(self.game_id),
            "user_id": str(self.user_id)
        }

    async def save(self) -> None:
        await self._controller.set(self._controller.key(self.game_id), self.to_json())

    async def clear(self) -> None:
        await self._controller.remove(self._controller.key(self.game_id))

    @property
    def controller(self) -> 'SingleDeviceGamesController':
        return self._controller
