from app.assets.controllers.redis.abstract import RedisController
from app.assets.filters.string import LocaleStr


class LocalesController(RedisController):
    def key(
            self,
            telegram_id: int
    ) -> str:
        return f"locale:{telegram_id}"

    async def create_locale(
            self,
            telegram_id: int,
            locale: str
    ) -> None:
        await self.set(self.key(telegram_id), locale)

    async def get_locale(
            self,
            telegram_id: int
    ) -> str | None:
        return await self.get(self.key(telegram_id))

    async def exists_locale(
            self,
            telegram_id: int
    ) -> bool:
        return await self.exists(self.key(telegram_id))

    async def remove_locale(
            self,
            telegram_id: int
    ) -> None:
        await self.remove(self.key(telegram_id))
