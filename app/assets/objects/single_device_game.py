from typing import ClassVar, Self, Dict, Any, Tuple
from uuid import UUID, uuid4

from pydantic import Field

from app.api.v1.exceptions.already_in_game import AlreadyInGameError
from app.assets.controllers.redis import RedisController
from app.assets.enums.category import Category
from app.assets.enums.spy_count import SpyCount
from app.assets.objects.redis import AbstractRedisObject
from app.assets.objects.secret_words_queue import SecretWordsQueue
from app.assets.objects.single_device_active_player import SingleDeviceActivePlayer


class SingleDeviceGame(AbstractRedisObject):
    """
    Represents a single-device game in a Redis database.
    """

    key: ClassVar[str] = "single_device_game"

    _players_controller: RedisController[SingleDeviceActivePlayer] | None = None
    """
    Redis controller instance for active players.
    """

    user_id: UUID
    """
    Host UUID.
    """

    player_amount: int
    """
    Count of players.
    """

    secret_word: str
    """
    Game's secret word tag.
    """

    category: Category = Category.GENERAL
    """
    Secret word category.
    """

    spy_indices: Tuple[int, ...] | None = None
    """
    Indices of spies in game.
    """

    spy_count: SpyCount
    """
    Count of spies.
    """

    game_id: UUID = Field(default_factory=uuid4)
    """
    UUID.
    """

    def model_post_init(
            self,
            context: Any
    ) -> None:
        """
        Set a random spy indices after an object initialization.
        """

        if self.spy_indices is None:
            self.spy_indices = self.spy_count.get_indices(self.player_amount)

    @property
    def primary_key(self) -> UUID:
        """
        Primary key represented by a game UUID.
        :return: Game UUID.
        """

        return self.game_id

    @property
    def players_controller(self) -> RedisController[SingleDeviceActivePlayer]:
        """
        Players controller instance. A private parameter must be set after an object initialization.

        :raise ValueError: If a controller instance is not set.
        :return: Players controller instance.
        """

        if self._players_controller is None:
            raise ValueError("Players controller is not set")
        return self._players_controller

    @classmethod
    def new(
            cls,
            user_id: UUID,
            player_amount: int,
            secret_word: str,
            category: Category,
            spy_count: SpyCount,
            *,
            controller: RedisController[Self],
            players_controller: RedisController[SingleDeviceActivePlayer]
    ) -> Self:
        """
        Generate a new single-device game instance using only required parameters.

        :param user_id: Host UUID.
        :param player_amount: Count of players.
        :param secret_word: Game's secret word tag.
        :param category: Secret word category.
        :param spy_count: Count of spies.
        :param controller: Single-device games controller instance.
        :param players_controller: Players controller instance.
        :return: New single-device game instance.
        """

        game = cls(
            user_id=user_id,
            player_amount=player_amount,
            secret_word=secret_word,
            category=category,
            spy_count=spy_count
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
        """
        Reconstruct a single-device game instance from a JSON-Serialized dictionary and a controller instances.

        :param data: Dictionary to reconstruct an object instance.
        :param controller: Single-device games controller instance.
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
            user_id: UUID,
            player_amount: int,
            category: Category = Category.GENERAL,
            spy_count: SpyCount = SpyCount.SINGLE,
            *,
            games_controller: RedisController[Self],
            players_controller: RedisController[SingleDeviceActivePlayer],
            secret_words_controller: RedisController[SecretWordsQueue]
    ) -> Self:
        """
        Host a new game.

        Saves a game object, player object, and updated secret words queue in Redis,
        and returns a new single-device game instance.

        :param user_id: Host UUID.
        :param player_amount: Count of players.
        :param category: Secret word category.
        :param spy_count: Count of spies.
        :param games_controller: Single-device games controller instance.
        :param players_controller: Players controller instance.
        :param secret_words_controller: Secret words controller instance.

        :raise AlreadyInGameError: If user is already in game.
        :return: New single-device game instance.
        """

        if await players_controller.exists(user_id):
            raise AlreadyInGameError("You are already in game")

        queue: SecretWordsQueue | None = await secret_words_controller.get(user_id)
        if queue is None:
            queue = SecretWordsQueue.new(
                user_id,
                controller=secret_words_controller
            )
        secret_word: str = await queue.get_unique_word(category)

        game = cls.new(
            user_id=user_id,
            player_amount=player_amount,
            secret_word=secret_word,
            category=category,
            spy_count=spy_count,
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
        """
        Unhost an existing game.

        Clears a game object and player object from Redis.
        """

        await self.players_controller.remove(self.user_id)
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
        and returns a new single-device game instance.

        :param game: Single-device game instance.
        :param secret_words_controller: Secret words controller instance.
        :return: New single-device game instance.
        """

        await game.unhost()

        return await cls.host(
            game.user_id,
            game.player_amount,
            game.category,
            game.spy_count,
            games_controller=game.controller,
            players_controller=game.players_controller,
            secret_words_controller=secret_words_controller
        )
