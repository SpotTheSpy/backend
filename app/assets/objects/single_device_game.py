from random import randint
from typing import Dict, Any, ClassVar
from uuid import UUID, uuid4

from pydantic import Field

from app.assets.controllers.redis import RedisController
from app.assets.objects.redis import AbstractRedisObject


class SingleDeviceGame(AbstractRedisObject):
    key: ClassVar[str] = "single_device_game"

    user_id: UUID
    player_amount: int
    secret_word: str

    game_id: UUID = Field(default_factory=uuid4)
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
            controller: RedisController['SingleDeviceGame']
    ) -> 'SingleDeviceGame':
        return cls(
            user_id=user_id,
            player_amount=player_amount,
            secret_word=secret_word,
            _controller=controller
        )
