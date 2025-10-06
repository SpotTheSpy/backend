from typing import Dict, Any
from uuid import UUID

from app.assets.controllers.redis.redis import RedisController
from app.assets.objects.multi_device_active_player import MultiDeviceActivePlayer


class MultiDevicePlayersController(RedisController):
    def key(
            self,
            player_id: UUID
    ) -> str:
        return f"multi_device_player:{player_id}"

    async def create_player(
            self,
            game_id: UUID,
            user_id: UUID
    ) -> MultiDeviceActivePlayer:
        player = MultiDeviceActivePlayer.new(
            game_id=game_id,
            user_id=user_id,
            controller=self
        )

        await player.save()

        return player

    async def get_player(
            self,
            user_id: UUID
    ) -> MultiDeviceActivePlayer | None:
        player_json: Dict[str, Any] = await self.get(self.key(user_id))

        if player_json is None:
            return

        return MultiDeviceActivePlayer.from_json(player_json, controller=self)

    async def exists_player(
            self,
            user_id: UUID
    ) -> bool:
        return await self.exists(self.key(user_id))

    async def remove_player(
            self,
            user_id: UUID
    ) -> None:
        player: MultiDeviceActivePlayer | None = await self.get_player(user_id)

        if player is None:
            return

        await player.clear()
