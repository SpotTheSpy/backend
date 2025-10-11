import asyncio
from base64 import urlsafe_b64encode
from random import randint
from typing import Any, ClassVar, Dict, List, Self
from uuid import UUID, uuid4

from celery.result import AsyncResult
from pydantic import Field, field_validator, field_serializer

from app.api.v1.exceptions.already_exists import AlreadyExistsError
from app.api.v1.exceptions.already_in_game import AlreadyInGameError
from app.api.v1.exceptions.game_has_already_started import GameHasAlreadyStartedError
from app.api.v1.exceptions.invalid_player_amount import InvalidPlayerAmountError
from app.api.v1.exceptions.not_in_game import NotInGameError
from app.assets.controllers.redis import RedisController
from app.assets.controllers.s3 import S3Controller
from app.assets.enums.payload_type import PayloadType
from app.assets.enums.player_role import PlayerRole
from app.assets.objects.multi_device_active_player import MultiDeviceActivePlayer
from app.assets.objects.multi_device_player import MultiDevicePlayer
from app.assets.objects.qr_code import QRCode
from app.assets.objects.redis import AbstractRedisObject
from app.assets.objects.secret_words_queue import SecretWordsQueue
from app.assets.parameters import Parameters
from app.workers.tasks import generate_qr_code_task


class MultiDeviceGame(AbstractRedisObject):
    key: ClassVar[str] = "multi_device_game"

    _players_controller: RedisController[MultiDeviceActivePlayer] | None = None

    host_id: UUID
    player_amount: int
    secret_word: str
    qr_code_url: str | None = None

    game_id: UUID = Field(default_factory=uuid4)
    has_started: bool = False

    players: Dict[UUID, MultiDevicePlayer] = Field(default_factory=dict)

    @field_validator("players", mode="before")
    def validate_players(cls, data: List[Dict[str, Any]]) -> Dict[UUID, MultiDevicePlayer]:
        return {
            player.user_id: player
            for player in map(MultiDevicePlayer.from_json, data)
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
    def players_controller(self) -> RedisController[MultiDeviceActivePlayer]:
        if self._players_controller is None:
            raise ValueError("Players controller is not set")
        return self._players_controller

    @property
    def join_url(self) -> str:
        payload: str = f"{PayloadType.JOIN}:{self.game_id}"
        encoded_payload: str = urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8").replace("=", "")
        return Parameters.TELEGRAM_BOT_START_URL.format(payload=encoded_payload)

    @classmethod
    def new(
            cls,
            host_id: UUID,
            player_amount: int,
            secret_word: str,
            qr_code_url: str | None = None,
            *,
            controller: RedisController[Self],
            players_controller: RedisController[MultiDeviceActivePlayer]
    ) -> Self:
        game = cls(
            host_id=host_id,
            player_amount=player_amount,
            secret_word=secret_word,
            qr_code_url=qr_code_url
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
            players_controller: RedisController[MultiDeviceActivePlayer],
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
            host_id: UUID,
            telegram_id: int,
            first_name: str,
            player_amount: int,
            *,
            games_controller: RedisController[Self],
            players_controller: RedisController[MultiDeviceActivePlayer],
            secret_words_controller: RedisController[SecretWordsQueue],
            players: Dict[UUID, MultiDevicePlayer] | None = None
    ) -> Self:
        if await players_controller.exists(host_id):
            raise AlreadyInGameError("You are already in game")

        queue: SecretWordsQueue | None = await secret_words_controller.get(host_id)
        if queue is None:
            queue = SecretWordsQueue.new(
                host_id,
                controller=secret_words_controller
            )
        secret_word: str = await queue.get_unique_word()

        game = cls.new(
            host_id=host_id,
            player_amount=player_amount,
            secret_word=secret_word,
            controller=games_controller,
            players_controller=players_controller
        )

        if players is not None:
            game.players = players

        game.players[host_id] = MultiDevicePlayer.new(
            user_id=host_id,
            telegram_id=telegram_id,
            first_name=first_name
        )

        await game.save()

        for player in game.players.values():
            await MultiDeviceActivePlayer.new(
                game_id=game.game_id,
                user_id=player.user_id,
                controller=players_controller
            ).save()

        await queue.save()

        return game

    async def unhost(self) -> None:
        for player in self.players.values():
            await self.players_controller.remove(player.user_id)

        await self.clear()

    @classmethod
    async def rehost(
            cls,
            game: Self,
            *,
            secret_words_controller: RedisController[SecretWordsQueue]
    ) -> Self:
        await game.unhost()

        host: MultiDevicePlayer = game.players.get(game.host_id)

        return await cls.host(
            host.user_id,
            host.telegram_id,
            host.first_name,
            game.player_amount,
            games_controller=game.controller,
            players_controller=game.players_controller,
            secret_words_controller=secret_words_controller,
            players=game.players
        )

    async def join(
            self,
            user_id: UUID,
            telegram_id: int,
            first_name: str
    ) -> None:
        if self.has_started:
            raise GameHasAlreadyStartedError("Game has already started")
        if user_id in self.players:
            raise AlreadyInGameError("You are already in game")
        if len(self.players) >= self.player_amount:
            raise InvalidPlayerAmountError("Game has too many players")

        self.players[user_id] = MultiDevicePlayer.new(
            user_id=user_id,
            telegram_id=telegram_id,
            first_name=first_name
        )

        player = MultiDeviceActivePlayer.new(
            game_id=self.game_id,
            user_id=user_id,
            controller=self.players_controller
        )

        await self.save()
        await player.save()

    async def leave(
            self,
            user_id: UUID
    ) -> None:
        if user_id not in self.players:
            raise NotInGameError("You are not in game")

        self.players.pop(user_id)

        await self.players_controller.remove(user_id)
        await self.save()

    async def start(self) -> None:
        if self.has_started:
            raise GameHasAlreadyStartedError("Game has already started")
        if len(self.players) < Parameters.MIN_PLAYER_AMOUNT:
            raise InvalidPlayerAmountError("Game has too few players")

        self.has_started = True
        spy_index: int = randint(0, len(self.players) - 1)

        for index, player in enumerate(self.players.values()):
            if index == spy_index:
                player.role = PlayerRole.SPY
            else:
                player.role = PlayerRole.CITIZEN

        await self.save()

    async def generate_qr_code(
            self,
            *,
            qr_codes_controller: S3Controller[QRCode]
    ) -> None:
        if await qr_codes_controller.exists(f"{self.game_id}.jpg"):
            return

        task: AsyncResult = await asyncio.to_thread(generate_qr_code_task.delay, self.join_url)
        qr_code = QRCode.new(
            str(self.game_id),
            await asyncio.to_thread(task.get, timeout=10, **{})
        )

        await qr_codes_controller.set(qr_code)
        self.qr_code_url = await qr_codes_controller.url(qr_code.primary_key)

        await self.save()
