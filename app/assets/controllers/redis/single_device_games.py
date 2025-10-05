from typing import Dict, Any, Tuple, List
from uuid import UUID

from redis.asyncio import Redis

from app.assets.controllers.redis.abstract import RedisController
from app.assets.controllers.redis.single_device_players import SingleDevicePlayersController
from app.assets.objects.single_device_game import SingleDeviceGame
from app.assets.objects.single_device_active_player import SingleDeviceActivePlayer


class SingleDeviceGamesController(RedisController):
    def __init__(
            self,
            redis: Redis
    ) -> None:
        super().__init__(redis)

        self._players_controller = SingleDevicePlayersController(redis)

    def key(
            self,
            game_id: UUID
    ) -> str:
        return f"single_device_game:{game_id}"

    @property
    def players_controller(self) -> SingleDevicePlayersController:
        return self._players_controller

    async def create_game(
            self,
            user_id: UUID,
            player_amount: int,
            secret_word: str
    ) -> SingleDeviceGame:
        game = SingleDeviceGame.new(
            user_id=user_id,
            player_amount=player_amount,
            secret_word=secret_word,
            controller=self
        )

        await game.save()

        await self.players_controller.create_player(
            user_id=user_id,
            game_id=game.game_id
        )

        return game

    async def get_games(
            self,
            limit: int = 100,
            offset: int = 0,
    ) -> Tuple[SingleDeviceGame, ...]:
        games: List[SingleDeviceGame] = []

        for key in await self.get_keys(pattern="single_device_game", limit=limit, offset=offset):
            games.append(
                SingleDeviceGame.from_json(
                    await self.get(key, exact_key=True),
                    controller=self
                )
            )

        return tuple(games)

    async def get_game(
            self,
            game_id: UUID
    ) -> SingleDeviceGame | None:
        game_json: Dict[str, Any] | None = await self.get(self.key(game_id))

        if game_json is None:
            return

        return SingleDeviceGame.from_json(game_json, controller=self)

    async def get_game_by_player(
            self,
            user_id: UUID
    ) -> SingleDeviceGame | None:
        player: SingleDeviceActivePlayer | None = await self.players_controller.get_player(user_id)

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
        game: SingleDeviceGame | None = await self.get_game(game_id)

        if game is None:
            return

        await self.players_controller.remove_player(game.user_id)
        await game.clear()
