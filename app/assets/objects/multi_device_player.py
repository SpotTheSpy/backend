from typing import Any, Self
from uuid import UUID

from app.assets.enums.player_role import PlayerRole
from app.assets.objects.abstract import AbstractObject


class MultiDevicePlayer(AbstractObject):
    """
    Represents a multi-device player inside a game object.
    """

    user_id: UUID
    """
    UUID.
    """

    telegram_id: int
    """
    User's telegram ID.
    """

    first_name: str
    """
    User's first name.
    """

    role: PlayerRole | None = None
    """
    User's role in game.
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
            user_id: UUID,
            telegram_id: int,
            first_name: str
    ) -> Self:
        """
        Generate a new multi-device player instance using only required parameters.

        :param user_id: User UUID.
        :param telegram_id: User's telegram ID.
        :param first_name: User's first name.
        :return: New multi-device player instance.
        """

        return cls(
            user_id=user_id,
            telegram_id=telegram_id,
            first_name=first_name
        )
