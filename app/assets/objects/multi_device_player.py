from typing import Any, Dict, TYPE_CHECKING, Optional
from uuid import UUID

from pydantic import ValidationError

from app.assets.enums.player_role import PlayerRole
from app.assets.objects.abstract import AbstractObject

if TYPE_CHECKING:
    from app.assets.objects.multi_device_game import MultiDeviceGame
else:
    MultiDeviceGame = Any


class MultiDevicePlayer(AbstractObject):
    user_id: UUID
    telegram_id: int
    first_name: str
    _game: Optional['MultiDeviceGame']

    role: PlayerRole | None = None

    @property
    def primary_key(self) -> Any:
        return self.user_id

    @property
    def game(self) -> 'MultiDeviceGame':
        if self._game is None:
            raise ValueError("Game is not set")
        return self._game

    @game.setter
    def game(self, value: 'MultiDeviceGame') -> None:
        if value is None:
            raise ValueError("Game cannot be set to None")
        self._game = value

    @property
    def is_host(self) -> bool:
        return self.user_id == self.game.host_id

    @classmethod
    def new(
            cls,
            user_id: UUID,
            telegram_id: int,
            first_name: str,
            *,
            game: 'MultiDeviceGame'
    ) -> 'MultiDevicePlayer':
        return cls(
            user_id=user_id,
            telegram_id=telegram_id,
            first_name=first_name,
            _game=game
        )

    @classmethod
    def from_json_and_game(
            cls,
            data: Dict[str, Any],
            *,
            game: Optional['MultiDeviceGame'] = None
    ) -> Optional['MultiDevicePlayer']:
        try:
            value = cls.model_validate(data)
            value._game = game

            return value
        except ValidationError:
            pass
