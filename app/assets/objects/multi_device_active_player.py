from typing import Any, Dict, TYPE_CHECKING
from uuid import UUID

from pydantic.dataclasses import dataclass

from app.assets.objects.base import BaseObject

if TYPE_CHECKING:
    from app.assets.controllers.redis.multi_device_players import MultiDevicePlayersController
else:
    MultiDevicePlayersController = Any


@dataclass
class MultiDeviceActivePlayer(BaseObject):
    game_id: UUID
    user_id: UUID

    _controller: 'MultiDevicePlayersController'

    @classmethod
    def new(
            cls,
            game_id: UUID,
            user_id: UUID,
            *,
            controller: 'MultiDevicePlayersController'
    ) -> 'MultiDeviceActivePlayer':
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
            controller: 'MultiDevicePlayersController'
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
    def controller(self) -> 'MultiDevicePlayersController':
        return self._controller
