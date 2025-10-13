from typing import Any, ClassVar, Self
from uuid import UUID

from app.assets.controllers.redis import RedisController
from app.assets.objects.redis import AbstractRedisObject


class MultiDeviceActivePlayer(AbstractRedisObject):
    """
    Represents a multi-device active player in a redis Database.
    """

    key: ClassVar[str] = "multi_device_player"

    game_id: UUID
    """
    Game UUID.
    """

    user_id: UUID
    """
    User UUID.
    """

    @property
    def primary_key(self) -> Any:
        """
        Primary key represented by a user UUID.
        :return: User UUID.
        """

        return self.user_id

    @classmethod
    def new(
            cls,
            game_id: UUID,
            user_id: UUID,
            *,
            controller: RedisController[Self]
    ) -> Self:
        """
        Generate a new multi-device player instance using only required parameters.

        :param game_id: Game UUID.
        :param user_id: User UUID.
        :param controller: Players controller instance.
        :return: New multi-device player instance.
        """

        player = cls(
            game_id=game_id,
            user_id=user_id
        )
        player._controller = controller

        return player
