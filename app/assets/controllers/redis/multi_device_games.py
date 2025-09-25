from typing import Dict, Any, Tuple, List
from uuid import UUID

from redis.asyncio import Redis

from app.assets.controllers.redis.abstract import RedisController
from app.assets.controllers.redis.multi_device_players import MultiDevicePlayersController
from app.assets.data.secret_words_controller import SecretWordsController
from app.assets.objects.multi_device_player import MultiDevicePlayer
from app.assets.objects.multi_device_game import MultiDeviceGame


class MultiDeviceGamesController(RedisController):
    def __init__(
            self,
            redis: Redis
    ) -> None:
        super().__init__(redis)

        self._players_controller = MultiDevicePlayersController(redis)

    def key(
            self,
            game_id: UUID
    ) -> str:
        return f"multi_device_game:{game_id}"

    @property
    def players_controller(self) -> MultiDevicePlayersController:
        return self._players_controller

    async def create_game(
            self,
            user_id: UUID,
            telegram_id: int,
            player_amount: int
    ) -> MultiDeviceGame:
        secret_word: str = SecretWordsController.get_random_secret_word()

        game = MultiDeviceGame.new(
            user_id=user_id,
            telegram_id=telegram_id,
            player_amount=player_amount,
            secret_word=secret_word,
            controller=self
        )

        await game.save()

        await self.players_controller.create_player(
            MultiDevicePlayer(
                user_id=user_id,
                game_id=game.game_id
            )
        )

        return game

    async def get_games(
            self,
            limit: int = 100,
            offset: int = 0,
    ) -> Tuple[MultiDeviceGame, ...]:
        games: List[MultiDeviceGame] = []

        for key in await self.get_keys(pattern="multi_device_game", limit=limit, offset=offset):
            games.append(
                MultiDeviceGame.from_json(
                    await self.get(key, exact_key=True),
                    controller=self
                )
            )

        return tuple(games)

    async def get_game(
            self,
            game_id: UUID
    ) -> MultiDeviceGame | None:
        game_json: Dict[str, Any] | None = await self.get(self.key(game_id))

        if game_json is None:
            return

        return MultiDeviceGame.from_json(game_json, controller=self)

    async def get_game_by_player(
            self,
            user_id: UUID
    ) -> MultiDeviceGame | None:
        player: MultiDevicePlayer | None = await self.players_controller.get_player(user_id)

        if player is None:
            return

        return await self.get_game(player.game_id)

    async def exists_game(
            self,
            game_id: UUID
    ) -> bool:
        return await self.exists(self.key(game_id))

    async def remove_game(
            self,
            game_id: UUID
    ) -> None:
        game: MultiDeviceGame = await self.get_game(game_id)

        await self.players_controller.remove_player(game.user_id)

        await game.clear()
