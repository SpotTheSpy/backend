from typing import Any
from uuid import UUID

from app.assets.enums.player_role import PlayerRole
from app.assets.objects.abstract import AbstractObject


class MultiDevicePlayer(AbstractObject):
    user_id: UUID
    telegram_id: int
    first_name: str
    role: PlayerRole | None = None

    @property
    def primary_key(self) -> Any:
        return self.user_id

    @classmethod
    def new(
            cls,
            user_id: UUID,
            telegram_id: int,
            first_name: str
    ) -> 'MultiDevicePlayer':
        return cls(
            user_id=user_id,
            telegram_id=telegram_id,
            first_name=first_name
        )
