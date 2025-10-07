from base64 import urlsafe_b64encode
from random import randint
from typing import Any, ClassVar, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import Field, field_validator, field_serializer

from app.api.v1.exceptions.already_in_game import AlreadyInGameError
from app.api.v1.exceptions.game_has_already_started import GameHasAlreadyStartedError
from app.api.v1.exceptions.invalid_player_amount import InvalidPlayerAmountError
from app.api.v1.exceptions.not_in_game import NotInGameError
from app.assets.controllers.redis import RedisController
from app.assets.controllers.s3.qr_codes import QRCodesController
from app.assets.enums.payload_type import PayloadType
from app.assets.enums.player_role import PlayerRole
from app.assets.objects.multi_device_active_player import MultiDeviceActivePlayer
from app.assets.objects.multi_device_player import MultiDevicePlayer
from app.assets.objects.redis import AbstractRedisObject
from app.assets.objects.secret_words_queue import SecretWordsQueue
from app.assets.parameters import Parameters


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

    def __post_init__(self) -> None:
        for player in self.players.values():
            player.game = self

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
    def players_controller(self) -> RedisController[MultiDeviceActivePlayer]:
        if self._players_controller is None:
            raise ValueError("Players controller is not set")
        return self._players_controller

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
            qr_code_url: str | None = None,
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
    async def host(
            cls,
            host_id: UUID,
            telegram_id: int,
            first_name: str,
            player_amount: int,
            *,
            games_controller: RedisController['MultiDeviceGame'],
            players_controller: RedisController[MultiDeviceActivePlayer],
            secret_words_controller: RedisController[SecretWordsQueue],
            players: Dict[UUID, MultiDevicePlayer] | None = None
    ) -> 'MultiDeviceGame':
        queue: SecretWordsQueue | None = await secret_words_controller.get(host_id)
        if queue is None:
            queue = SecretWordsQueue.new(
                host_id,
                controller=secret_words_controller
            )
        secret_word: str = await queue.get_unique_word()

        await cls._unhost_game(
            host_id,
            games_controller=games_controller,
            players_controller=players_controller,
            remove_active_player=False
        )

        game = cls.new(
            host_id=host_id,
            player_amount=player_amount,
            secret_word=secret_word,
            controller=games_controller
        )
        if players is not None:
            game.players = players
        game.players[host_id] = MultiDevicePlayer.new(
            user_id=host_id,
            telegram_id=telegram_id,
            first_name=first_name,
            game=game
        )

        player = MultiDeviceActivePlayer.new(
            game_id=game.game_id,
            user_id=host_id,
            controller=players_controller
        )

        await game.save()
        await player.save()
        await queue.save()

        return game

    async def join(
            self,
            user_id: UUID,
            telegram_id: int,
            first_name: str,
            *,
            players_controller: RedisController[MultiDeviceActivePlayer]
    ) -> None:
        if self.has_started:
            raise GameHasAlreadyStartedError("Game has already started")
        if user_id in self.players:
            raise AlreadyInGameError("You are already in game")
        if self.player_amount >= Parameters.MAX_PLAYER_AMOUNT:
            raise InvalidPlayerAmountError("Game has too many players")

        self.players[user_id] = MultiDevicePlayer.new(
            user_id=user_id,
            telegram_id=telegram_id,
            first_name=first_name,
            game=self
        )

        player = MultiDeviceActivePlayer.new(
            game_id=self.game_id,
            user_id=user_id,
            controller=players_controller
        )

        await self.save()
        await player.save()

    async def leave(
            self,
            user_id: UUID,
            *,
            players_controller: RedisController[MultiDeviceActivePlayer]
    ) -> None:
        if user_id not in self.players:
            raise NotInGameError("You are not in game")

        self.players.pop(user_id)

        await players_controller.remove(user_id)
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

    @staticmethod
    async def _unhost_game(
            host_id: UUID,
            *,
            games_controller: RedisController['MultiDeviceGame'],
            players_controller: RedisController[MultiDeviceActivePlayer],
            remove_active_player: bool = True
    ) -> None:
        player: MultiDeviceActivePlayer | None = await players_controller.get(host_id)

        if player is not None:
            if remove_active_player:
                await players_controller.remove(player.user_id)
            await games_controller.remove(player.game_id)
