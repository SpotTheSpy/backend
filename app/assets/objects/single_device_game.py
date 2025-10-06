from dataclasses import field as dataclass_field
from random import randint
from typing import Dict, Any, ClassVar
from uuid import UUID, uuid4

from pydantic.dataclasses import dataclass

from app.assets.controllers.redis import RedisController
from app.assets.objects.redis import AbstractRedisObject


@dataclass
class SingleDeviceGame(AbstractRedisObject):
    key: ClassVar[str] = "single_device_game"

    user_id: UUID
    player_amount: int
    secret_word: str

    game_id: UUID = dataclass_field(default_factory=uuid4)
    spy_index: int | None = None

    def __post_init__(self) -> None:
        if self.spy_index is None:
            self.spy_index = randint(0, self.player_amount - 1)

    @property
    def primary_key(self) -> UUID:
        return self.game_id

    @classmethod
    def new(
            cls,
            user_id: UUID,
            player_amount: int,
            secret_word: str,
            *,
            controller: RedisController['SingleDeviceGame'],
    ) -> 'SingleDeviceGame':
        return cls(
            user_id=user_id,
            player_amount=player_amount,
            secret_word=secret_word,
            _controller=controller
        )

    @classmethod
    def from_json(
            cls,
            data: Dict[str, Any],
            *,
            controller: RedisController['SingleDeviceGame']
    ) -> 'SingleDeviceGame':
        return cls(**data, _controller=controller)

    def to_json(self) -> Dict[str, Any]:
        return {
            "game_id": str(self.game_id),
            "user_id": str(self.user_id),
            "player_amount": self.player_amount,
            "secret_word": self.secret_word,
            "spy_index": self.spy_index
        }
