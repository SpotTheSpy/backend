from dataclasses import field as dataclass_field
from random import randint
from typing import Dict, Any, TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic.dataclasses import dataclass

from app.assets.objects.redis import RedisObject

if TYPE_CHECKING:
    from app.assets.controllers.redis.single_device_games import SingleDeviceGamesController
else:
    SingleDeviceGamesController = Any


@dataclass
class SingleDeviceGame(RedisObject):
    user_id: UUID
    telegram_id: int
    player_amount: int
    secret_word: str

    _controller: 'SingleDeviceGamesController'

    game_id: UUID = dataclass_field(default_factory=uuid4)
    spy_index: int | None = None

    def post_init(self) -> None:
        if self.spy_index is None:
            self.spy_index = randint(0, self.player_amount - 1)

    @classmethod
    def new(
            cls,
            user_id: UUID,
            telegram_id: int,
            player_amount: int,
            secret_word: str,
            *,
            controller: 'SingleDeviceGamesController',
    ) -> 'SingleDeviceGame':
        return cls(
            user_id=user_id,
            telegram_id=telegram_id,
            player_amount=player_amount,
            secret_word=secret_word,
            _controller=controller
        )

    @classmethod
    def from_json(
            cls,
            data: Dict[str, Any],
            *,
            controller: 'SingleDeviceGamesController'
    ) -> 'SingleDeviceGame':
        return cls(**data, _controller=controller)

    def to_json(self) -> Dict[str, Any]:
        return {
            "game_id": str(self.game_id),
            "user_id": str(self.user_id),
            "telegram_id": self.telegram_id,
            "player_amount": self.player_amount,
            "secret_word": self.secret_word,
            "spy_index": self.spy_index
        }

    async def save(self) -> None:
        await self._controller.set(self._controller.key(self.game_id), self.to_json())

    async def clear(self) -> None:
        await self._controller.remove(self._controller.key(self.game_id))

    @property
    def controller(self) -> 'SingleDeviceGamesController':
        return self._controller
