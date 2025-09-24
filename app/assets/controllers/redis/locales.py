from uuid import UUID

from app.assets.controllers.redis.abstract import RedisController


class LocalesController(RedisController):
    def key(
            self,
            user_id: UUID
    ) -> str:
        return f"locale:{user_id}"

    async def create_locale(
            self,
            user_id: UUID,
            locale: str
    ) -> None:
        await self.set(self.key(user_id), locale)

    async def get_locale(
            self,
            user_id: UUID
    ) -> str | None:
        return await self.get(self.key(user_id))

    async def exists_locale(
            self,
            user_id: UUID
    ) -> bool:
        return await self.exists(self.key(user_id))

    async def remove_locale(
            self,
            user_id: UUID
    ) -> None:
        await self.remove(self.key(user_id))
