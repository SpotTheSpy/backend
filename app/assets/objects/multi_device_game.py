import asyncio
from base64 import urlsafe_b64encode
from random import randint
from typing import Any, ClassVar, Dict, List, Self
from uuid import UUID, uuid4

from celery.result import AsyncResult
from pydantic import Field, field_validator, field_serializer

from app.api.v1.exceptions.already_in_game import AlreadyInGameError
from app.api.v1.exceptions.game_has_already_started import GameHasAlreadyStartedError
from app.api.v1.exceptions.invalid_player_amount import InvalidPlayerAmountError
from app.api.v1.exceptions.not_in_game import NotInGameError
from app.assets.controllers.redis import RedisController
from app.assets.controllers.s3 import S3Controller
from app.assets.enums.category import Category
from app.assets.enums.payload import Payload
from app.assets.enums.player_role import PlayerRole
from app.assets.objects.multi_device_active_player import MultiDeviceActivePlayer
from app.assets.objects.multi_device_player import MultiDevicePlayer
from app.assets.objects.qr_code import QRCode
from app.assets.objects.redis import AbstractRedisObject
from app.assets.objects.secret_words_queue import SecretWordsQueue
from app.workers.tasks import generate_qr_code_task
from config import config


class MultiDeviceGame(AbstractRedisObject):
    """
    Represents a multi-device game in a Redis database.
    """

    key: ClassVar[str] = "multi_device_game"

    _players_controller: RedisController[MultiDeviceActivePlayer] | None = None
    """
    Redis controller instance for active players.
    """

    host_id: UUID
    """
    Host UUID.
    """

    player_amount: int
    """
    Count of max players who can join.
    """

    secret_word: str
    """
    Game's secret word tag.
    """

    category: Category = Category.GENERAL
    """
    Secret word category.
    """

    qr_code_url: str | None = None
    """
    QR code URL for a direct image download.
    """

    game_id: UUID = Field(default_factory=uuid4)
    """
    UUID.
    """

    has_started: bool = False
    """
    Is the game started.
    """

    players: Dict[UUID, MultiDevicePlayer] = Field(default_factory=dict)
    """
    Dictionary of all players.
    """

    @field_validator("players", mode="before")
    def validate_players(cls, data: List[Dict[str, Any]]) -> Dict[UUID, MultiDevicePlayer]:
        """
        Create a player dictionary from list.

        :param data: JSON-Serialized list of players.
        :return: Dictionary of players.
        """

        return {
            player.user_id: player
            for player in map(MultiDevicePlayer.from_json, data)
            if player is not None
        }

    @field_serializer("players")
    def serialize_players(self, players: Dict[UUID, MultiDevicePlayer]) -> List[Dict[str, Any]]:
        """
        Create a JSON-Serialized list of players.

        :param players: Dictionary of players.
        :return: JSON-Serialized list of players.
        """

        return [
            player.to_json()
            for player in players.values()
        ]

    @property
    def primary_key(self) -> Any:
        """
        Primary key represented by a game UUID.
        :return: Game UUID.
        """

        return self.game_id

    @property
    def players_controller(self) -> RedisController[MultiDeviceActivePlayer]:
        """
        Players controller instance. A private parameter must be set after an object initialization.

        :raise ValueError: If a controller instance is not set.
        :return: Players controller instance.
        """

        if self._players_controller is None:
            raise ValueError("Players controller is not set")
        return self._players_controller

    @property
    def join_url(self) -> str:
        """
        Deeplink start URL for joining game.

        :return: URL in a string format.
        """

        # Works the same as an aiogram payload encoding.
        payload: str = f"{Payload.JOIN}:{self.game_id}"
        encoded_payload: str = urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8").replace("=", "")
        return config.telegram_bot_start_url.format(payload=encoded_payload)

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
        """
        Generate a new multi-device game instance using only required parameters.

        :param host_id: Host UUID.
        :param player_amount: Count of max players who can join.
        :param secret_word: Game's secret word tag.
        :param qr_code_url: QR code URL for a direct image download, can be None.
        :param controller: Multi-device games controller instance.
        :param players_controller: Players controller instance.
        :return: New multi-device game instance.
        """

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
        """
        Reconstruct a multi-device game instance from a JSON-Serialized dictionary and a controller instances.

        :param data: Dictionary to reconstruct an object instance.
        :param controller: Multi-device games controller instance.
        :param players_controller: Players controller instance.
        :param kwargs: Any additional JSON-Serializable parameters.
        :return: An object instance if validated successfully, else None.
        """

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
        """
        Host a new game.

        Saves a game object, host player object, and updated secret words queue in Redis,
        and returns a new multi-device game instance.

        :param host_id: Host UUID.
        :param telegram_id: Host's telegram ID.
        :param first_name: Host's first name.
        :param player_amount: Count of max players who can join.
        :param games_controller: Multi-device games controller instance.
        :param players_controller: Players controller instance.
        :param secret_words_controller: Secret words queue controller instance.
        :param players: Dictionary of players, can be None.

        :raise AlreadyInGameError: If user is already in game.
        :return: New multi-device game instance.
        """

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
        """
        Unhost an existing game.

        Clears a game object and all player objects from Redis.
        """

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
        """
        Rehost an existing game.

        Recreates every object in Redis, updates secret words queue,
        and returns a new multi-device game instance.

        :param game: Multi-device game instance.
        :param secret_words_controller: Secret words controller instance.
        :return: New multi-device game instance.
        """

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
        """
        Join the game.

        Adds a player object to game, and saves an active player object to Redis.

        :param user_id: User UUID
        :param telegram_id: User's telegram ID.
        :param first_name: User's first name.

        :raise GameHasAlreadyStartedError: If the game has already started.
        :raise AlreadyInGameError: If a player has already joined.
        :raise InvalidPlayerAmountError: If a game has too many players.
        """

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
        """
        Leave the game.

        Removes a player object from game, and clears an active player object from Redis.

        :param user_id: User UUID.
        :raise NotInGameError: If a player has already left.
        """

        if user_id not in self.players:
            raise NotInGameError("You are not in game")

        self.players.pop(user_id)

        await self.players_controller.remove(user_id)
        await self.save()

    async def start(self) -> None:
        """
        Start the game.

        Attaches a role to every player.
        :raise GameHasAlreadyStartedError: If the game has already started.
        :raise InvalidPlayerAmountError: If a game has too few players to start.
        """

        if self.has_started:
            raise GameHasAlreadyStartedError("Game has already started")
        if len(self.players) < config.min_player_amount:
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
        """
        Generate a new QR-Code for the game. If QR-Code already exists, only a new URL will generate.

        :param qr_codes_controller: QR-Codes controller instance.
        """

        qr_code = QRCode.new(
            str(self.game_id),
            b""
        )

        if await qr_codes_controller.exists(qr_code.primary_key):
            self.qr_code_url = await qr_codes_controller.url(qr_code.primary_key)
            return

        task: AsyncResult = await asyncio.to_thread(generate_qr_code_task.delay, self.join_url)
        qr_code = QRCode.new(
            str(self.game_id),
            await asyncio.to_thread(task.get, timeout=10, **{})
        )

        await qr_codes_controller.set(qr_code)
        self.qr_code_url = await qr_codes_controller.url(qr_code.primary_key)

        await self.save()
