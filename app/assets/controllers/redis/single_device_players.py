from typing import Dict, Any
from uuid import UUID

from app.assets.controllers.redis.abstract import AbstractRedisController
from app.assets.objects.single_device_active_player import SingleDeviceActivePlayer


class SingleDevicePlayersController(AbstractRedisController):
    def key(
            self,
            player_id: UUID
    ) -> str:
        return f"single_device_player:{player_id}"

    async def create_player(
            self,
            game_id: UUID,
            user_id: UUID
    ) -> SingleDeviceActivePlayer:
        player = SingleDeviceActivePlayer.new(
            game_id=game_id,
            user_id=user_id,
            controller=self
        )

        await player.save()

        return player

    async def get_player(
            self,
            user_id: UUID
    ) -> SingleDeviceActivePlayer | None:
        player_json: Dict[str, Any] = await self.get(self.key(user_id))

        if player_json is None:
            return

        return SingleDeviceActivePlayer.from_json(player_json, controller=self)

    async def exists_player(
            self,
            user_id: UUID
    ) -> bool:
        return await self.exists(self.key(user_id))

    async def remove_player(
            self,
            user_id: UUID
    ) -> None:
        player: SingleDeviceActivePlayer | None = await self.get_player(user_id)

        if player is None:
            return

        await player.clear()
