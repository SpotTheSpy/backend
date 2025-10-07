from typing import ClassVar
from uuid import UUID

from app.assets.controllers.redis import RedisController
from app.assets.objects.redis import AbstractRedisObject


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
