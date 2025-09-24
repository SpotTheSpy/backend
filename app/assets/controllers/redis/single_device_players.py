from typing import Dict, Any
from uuid import UUID

from app.assets.controllers.redis.abstract import RedisController
from app.assets.objects.single_device_player import SingleDevicePlayer


class SingleDevicePlayersController(RedisController):
    def key(
            self,
            player_id: UUID
    ) -> str:
        return f"single_device_player:{player_id}"

    async def create_player(
            self,
            player: SingleDevicePlayer
    ) -> None:
        await self.set(self.key(player.user_id), player.to_json())

    async def get_player(
            self,
            user_id: UUID
    ) -> SingleDevicePlayer | None:
        player_json: Dict[str, Any] = await self.get(self.key(user_id))

        if player_json is None:
            return

        return SingleDevicePlayer.from_json(player_json)

    async def exists_player(
            self,
            user_id: UUID
    ) -> bool:
        return await self.exists(self.key(user_id))

    async def remove_player(
            self,
            user_id: UUID
    ) -> None:
        await self.remove(self.key(user_id))
