import asyncio
from dataclasses import field as dataclass_field
from random import randint
from typing import Dict, Any, TYPE_CHECKING, Optional, List
from uuid import UUID, uuid4

from pydantic.dataclasses import dataclass

from app.assets.controllers.context.multi_device_players import MultiDevicePlayers
from app.assets.enums.player_role import PlayerRole
from app.assets.objects.redis import RedisObject
from app.workers.tasks import save_multi_device_game, clear_multi_device_game

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
    qr_code_url: str | None = None

    players: MultiDevicePlayers = dataclass_field(default_factory=MultiDevicePlayers)

    def __post_init__(self) -> None:
        self.players.init(None, game=self)

    @classmethod
    def new(
            cls,
            host_id: UUID,
            player_amount: int,
            secret_word: str,
            qr_code_url: str | None = None,
            *,
            controller: 'MultiDeviceGamesController',
    ) -> 'MultiDeviceGame':
        return cls(
            host_id=host_id,
            player_amount=player_amount,
            secret_word=secret_word,
            qr_code_url=qr_code_url,
            _controller=controller
        )

    @classmethod
    def from_json(
            cls,
            data: Dict[str, Any],
            *,
            controller: 'MultiDeviceGamesController'
    ) -> Optional['MultiDeviceGame']:
        try:
            host_id: UUID = UUID(data.pop("host_id"))
        except (ValueError, KeyError):
            return

        players: List[Dict[str, Any]] = data.pop("players")

        game = cls(
            host_id=host_id,
            **data,
            _controller=controller
        )

        game.players.init(players, game=game)

        return game

    def to_json(self) -> Dict[str, Any]:
        return {
            "game_id": str(self.game_id),
            "host_id": str(self.host_id),
            "has_started": self.has_started,
            "player_amount": self.player_amount,
            "secret_word": self.secret_word,
            "qr_code_url": self.qr_code_url,
            "players": self.players.to_json()
        }

    async def save(self) -> None:
        await asyncio.to_thread(save_multi_device_game.delay, self.to_json())

    async def clear(self) -> None:
        await asyncio.to_thread(clear_multi_device_game.delay, self.to_json())

    @property
    def controller(self) -> 'MultiDeviceGamesController':
        return self._controller

    def start(self) -> None:
        self.has_started = True
        self.player_amount = self.players.size

        spy_index: int = randint(0, self.player_amount - 1)

        for index, player in enumerate(self.players.list):
            if index == spy_index:
                player.role = PlayerRole.SPY
            else:
                player.role = PlayerRole.CITIZEN
