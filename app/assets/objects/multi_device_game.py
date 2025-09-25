from dataclasses import field as dataclass_field
from random import randint
from typing import Dict, Any, TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic.dataclasses import dataclass

from app.assets.controllers.context.multi_device_players import MultiDevicePlayers
from app.assets.objects.redis import RedisObject

if TYPE_CHECKING:
    from app.assets.controllers.redis.multi_device_games import MultiDeviceGamesController
else:
    MultiDeviceGamesController = Any


@dataclass
class MultiDeviceGame(RedisObject):
    host_id: UUID
    player_amount: int
    secret_word: str

    _controller: 'MultiDeviceGamesController'

    game_id: UUID = dataclass_field(default_factory=uuid4)
    has_started: bool = False

    players: MultiDevicePlayers = dataclass_field(default_factory=MultiDevicePlayers)

    def __post_init__(self) -> None:
        self.players.init(None, game=self)

    @classmethod
    def new(
            cls,
            host_id: UUID,
            player_amount: int,
            secret_word: str,
            *,
            controller: 'MultiDeviceGamesController',
    ) -> 'MultiDeviceGame':
        return cls(
            host_id=host_id,
            player_amount=player_amount,
            secret_word=secret_word,
            _controller=controller
        )

    @classmethod
    def from_json(
            cls,
            data: Dict[str, Any],
            *,
            controller: 'MultiDeviceGamesController'
    ) -> 'MultiDeviceGame':
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
    def controller(self) -> 'MultiDeviceGamesController':
        return self._controller

    async def start(self) -> None:
        self.has_started = True
