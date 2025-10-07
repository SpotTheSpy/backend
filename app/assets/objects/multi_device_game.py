from base64 import urlsafe_b64encode
from random import randint
from typing import Any, ClassVar, Dict, List
from uuid import UUID, uuid4

from pydantic import Field, field_validator, field_serializer

from app.assets.controllers.redis import RedisController
from app.assets.enums.payload_type import PayloadType
from app.assets.enums.player_role import PlayerRole
from app.assets.objects.multi_device_player import MultiDevicePlayer
from app.assets.objects.redis import AbstractRedisObject
from app.assets.parameters import Parameters


class MultiDeviceGame(AbstractRedisObject):
    key: ClassVar[str] = "multi_device_game"

    host_id: UUID
    player_amount: int
    secret_word: str
    qr_code_url: str

    game_id: UUID = Field(default_factory=uuid4)
    has_started: bool = False

    players: Dict[UUID, MultiDevicePlayer] = Field(default_factory=dict)

    @field_validator("players", mode="before")
    def validate_players(cls, data: List[Dict[str, Any]]) -> Dict[UUID, MultiDevicePlayer]:
        return {
            player.user_id: player
            for player in map(MultiDevicePlayer.from_json_and_game, data)
            if player is not None
        }

    @field_serializer("players")
    def serialize_players(self, players: Dict[UUID, MultiDevicePlayer]) -> List[Dict[str, Any]]:
        return [
            player.to_json()
            for player in players.values()
        ]

    @property
    def primary_key(self) -> Any:
        return self.game_id

    @property
    def join_link(self) -> str:
        payload: str = f"{PayloadType.JOIN}:{self.game_id}"
        encoded_payload: str = urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8").replace("=", "")
        return Parameters.TELEGRAM_BOT_START_URL.format(payload=encoded_payload)

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
        self.player_amount = len(self.players)

        spy_index: int = randint(0, self.player_amount - 1)

        for index, player in enumerate(self.players.values()):
            if index == spy_index:
                player.role = PlayerRole.SPY
            else:
                player.role = PlayerRole.CITIZEN
