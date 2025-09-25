from typing import Any, Dict, TYPE_CHECKING, Optional
from uuid import UUID

from pydantic.dataclasses import dataclass

from app.assets.objects.base import BaseObject

if TYPE_CHECKING:
    from app.assets.objects.multi_device_game import MultiDeviceGame
else:
    MultiDeviceGame = Any


@dataclass
class MultiDevicePlayer(BaseObject):
    user_id: UUID
    first_name: str
    _game: 'MultiDeviceGame'

    @classmethod
    def new(
            cls,
            user_id: UUID,
            first_name: str,
            *,
            game: 'MultiDeviceGame'
    ) -> 'MultiDevicePlayer':
        return cls(
            user_id=user_id,
            first_name=first_name,
            _game=game
        )

    @classmethod
    def from_json(
            cls,
            data: Dict[str, Any],
            *,
            game: 'MultiDeviceGame'
    ) -> Optional['MultiDevicePlayer']:
        try:
            user_id: UUID = UUID(data.pop("user_id"))
        except (ValueError, KeyError):
            return

        return cls(
            user_id=user_id,
            **data,
            _game=game
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "first_name": self.first_name
        }

    @property
    def game(self) -> 'MultiDeviceGame':
        return self._game

    @property
    def is_host(self) -> bool:
        return self.user_id == self.game.host_id
