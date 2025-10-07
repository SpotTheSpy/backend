from random import randint
from typing import Any, ClassVar
from uuid import UUID, uuid4

from pydantic import Field

from app.assets.controllers.context import Context
from app.assets.controllers.redis import RedisController
from app.assets.enums.player_role import PlayerRole
from app.assets.objects.redis import AbstractRedisObject


class MultiDeviceGame(AbstractRedisObject):
    key: ClassVar[str] = "multi_device_game"

    host_id: UUID
    player_amount: int
    secret_word: str
    qr_code_url: str

    game_id: UUID = Field(default_factory=uuid4)
    has_started: bool = False

    players: Context = Field(default_factory=Context)

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

    def start(self) -> None:
        self.has_started = True
        self.player_amount = self.players.size

        spy_index: int = randint(0, self.player_amount - 1)

        for index, player in enumerate(self.players.list):
            if index == spy_index:
                player.role = PlayerRole.SPY
            else:
                player.role = PlayerRole.CITIZEN
