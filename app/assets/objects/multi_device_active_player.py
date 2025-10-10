from typing import Any, ClassVar, Self
from uuid import UUID

from app.assets.controllers.redis import RedisController
from app.assets.objects.redis import AbstractRedisObject


class MultiDeviceActivePlayer(AbstractRedisObject):
    key: ClassVar[str] = "multi_device_player"

    game_id: UUID
    user_id: UUID

    @property
    def primary_key(self) -> Any:
        return self.user_id

    @classmethod
    def new(
            cls,
            game_id: UUID,
            user_id: UUID,
            *,
            controller: RedisController[Self]
    ) -> Self:
        player = cls(
            game_id=game_id,
            user_id=user_id
        )
        player._controller = controller

        return player
