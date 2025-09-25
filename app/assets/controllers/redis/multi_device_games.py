from typing import Dict, Any, Tuple, List
from uuid import UUID

from redis.asyncio import Redis

from app.assets.controllers.redis.abstract import RedisController
from app.assets.controllers.redis.multi_device_players import MultiDevicePlayersController
from app.assets.data.secret_words_controller import SecretWordsController
from app.assets.objects.multi_device_active_player import MultiDeviceActivePlayer
from app.assets.objects.multi_device_game import MultiDeviceGame
from app.assets.objects.multi_device_player import MultiDevicePlayer


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
            host_id: UUID,
            first_name: str,
            player_amount: int
    ) -> MultiDeviceGame:
        secret_word: str = SecretWordsController.get_random_secret_word()

        game = MultiDeviceGame.new(
            host_id=host_id,
            player_amount=player_amount,
            secret_word=secret_word,
            controller=self
        )
        game.players.add(
            MultiDevicePlayer.new(
                user_id=host_id,
                first_name=first_name,
                game=game
            )
        )

        await game.save()

        await self.players_controller.create_player(
            MultiDeviceActivePlayer(
                user_id=host_id,
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
            game = MultiDeviceGame.from_json(
                await self.get(key, exact_key=True),
                controller=self
            )

            if game is None:
                continue

            games.append(game)

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
        player: MultiDeviceActivePlayer | None = await self.players_controller.get_player(user_id)

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

        for user_id in game.players.ids:
            await self.players_controller.remove_player(user_id)

        await game.clear()
