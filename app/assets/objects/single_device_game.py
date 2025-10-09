from random import randint
from typing import ClassVar, Self, Dict, Any
from uuid import UUID, uuid4

from pydantic import Field

from app.api.v1.exceptions.already_in_game import AlreadyInGameError
from app.assets.controllers.redis import RedisController
from app.assets.objects.redis import AbstractRedisObject
from app.assets.objects.secret_words_queue import SecretWordsQueue
from app.assets.objects.single_device_active_player import SingleDeviceActivePlayer


class SingleDeviceGame(AbstractRedisObject):
    key: ClassVar[str] = "single_device_game"

    _players_controller: RedisController[SingleDeviceActivePlayer] | None = None

    user_id: UUID
    player_amount: int
    secret_word: str
    spy_index: int

    game_id: UUID = Field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.spy_index is None:
            self.spy_index = randint(0, self.player_amount - 1)

    @property
    def primary_key(self) -> UUID:
        return self.game_id

    @property
    def players_controller(self) -> RedisController[SingleDeviceActivePlayer]:
        if self._players_controller is None:
            raise ValueError("Players controller is not set")
        return self._players_controller

    @classmethod
    def new(
            cls,
            user_id: UUID,
            player_amount: int,
            secret_word: str,
            *,
            controller: RedisController[Self],
            players_controller: RedisController[SingleDeviceActivePlayer]
    ) -> Self:
        game = cls(
            user_id=user_id,
            player_amount=player_amount,
            secret_word=secret_word,
            spy_index=randint(0, player_amount - 1)
        )
        game._controller = controller
        game._players_controller = players_controller

        return game

    @classmethod
    def from_json_and_controllers(
            cls,
            data: Dict[str, Any],
            *,
            controller: RedisController[Self],
            players_controller: RedisController[SingleDeviceActivePlayer],
            **kwargs
    ) -> Self:
        value = cls.from_json(data, **kwargs)

        if value is not None:
            value._controller = controller
            value._players_controller = players_controller

        return value

    @classmethod
    async def host(
            cls,
            user_id: UUID,
            player_amount: int,
            *,
            games_controller: RedisController[Self],
            players_controller: RedisController[SingleDeviceActivePlayer],
            secret_words_controller: RedisController[SecretWordsQueue]
    ) -> Self:
        if await players_controller.exists(user_id):
            raise AlreadyInGameError("You are already in game")

        queue: SecretWordsQueue | None = await secret_words_controller.get(user_id)
        if queue is None:
            queue = SecretWordsQueue.new(
                user_id,
                controller=secret_words_controller
            )
        secret_word: str = await queue.get_unique_word()

        game = cls.new(
            user_id=user_id,
            player_amount=player_amount,
            secret_word=secret_word,
            controller=games_controller,
            players_controller=players_controller
        )

        await game.save(expire=3600)

        await SingleDeviceActivePlayer.new(
            game_id=game.game_id,
            user_id=user_id,
            controller=players_controller
        ).save(expire=3600)

        await queue.save()

        return game

    async def unhost(self) -> None:
        await self.players_controller.remove(self.user_id)
        await self.clear()

    @classmethod
    async def rehost(
            cls,
            game: Self,
            *,
            secret_words_controller: RedisController[SecretWordsQueue]
    ) -> Self:
        await game.unhost()

        return await cls.host(
            game.user_id,
            game.player_amount,
            games_controller=game.controller,
            players_controller=game.players_controller,
            secret_words_controller=secret_words_controller
        )
