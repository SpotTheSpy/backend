from typing import Any, Dict, ClassVar
from uuid import UUID

from pydantic.dataclasses import dataclass

from app.assets.controllers.redis import RedisController
from app.assets.objects.redis import AbstractRedisObject


@dataclass
class SingleDeviceActivePlayer(AbstractRedisObject):
    key: ClassVar[str] = "single_device_player"

    game_id: UUID
    user_id: UUID

    @property
    def primary_key(self) -> UUID:
        return self.user_id

    @classmethod
    def new(
            cls,
            game_id: UUID,
            user_id: UUID,
            *,
            controller: RedisController['SingleDeviceActivePlayer']
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
            controller: RedisController['SingleDeviceActivePlayer']
    ) -> Any:
        return cls(**data, _controller=controller)

    def to_json(self) -> Dict[str, Any]:
        return {
            "game_id": str(self.game_id),
            "user_id": str(self.user_id)
        }
