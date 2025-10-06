from dataclasses import field as dataclass_field
from random import randint
from typing import Dict, Any, Optional, List, ClassVar
from uuid import UUID, uuid4

from pydantic.dataclasses import dataclass

from app.assets.controllers.context.multi_device_players import MultiDevicePlayers
from app.assets.controllers.redis import RedisController
from app.assets.enums.player_role import PlayerRole
from app.assets.objects.redis import AbstractRedisObject


@dataclass
class MultiDeviceGame(AbstractRedisObject):
    key: ClassVar[str] = "multi_device_game"

    host_id: UUID
    player_amount: int
    secret_word: str
    qr_code_url: str

    game_id: UUID = dataclass_field(default_factory=uuid4)
    has_started: bool = False

    players: MultiDevicePlayers = dataclass_field(default_factory=MultiDevicePlayers)

    def __post_init__(self) -> None:
        self.players.init(None, game=self)

    @property
    def primary_key(self) -> Any:
        return self.game_id

    @classmethod
    def new(
            cls,
            host_id: UUID,
            player_amount: int,
            secret_word: str,
            qr_code_url: str,
            *,
            controller: RedisController['MultiDeviceGame']
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
            controller: RedisController['MultiDeviceGame']
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

    def start(self) -> None:
        self.has_started = True
        self.player_amount = self.players.size

        spy_index: int = randint(0, self.player_amount - 1)

        for index, player in enumerate(self.players.list):
            if index == spy_index:
                player.role = PlayerRole.SPY
            else:
                player.role = PlayerRole.CITIZEN
