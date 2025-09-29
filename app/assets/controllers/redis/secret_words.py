from random import choice
from typing import List, Set
from uuid import UUID

from app.assets.controllers.redis.abstract import RedisController


class SecretWordsController(RedisController):
    _FILE_PATH: str = "app/assets/data/secret_words.txt"
    _GUARANTEE_UNIQUE_COUNT: int = 20

    with open(_FILE_PATH, "r", encoding="utf-8") as file:
        _SECRET_WORDS: List[str] = file.read().splitlines()

    def key(
            self,
            user_id: UUID
    ) -> str:
        return f"secret_words:{user_id}"

    async def get_random_secret_word(
            self,
            user_id: UUID
    ) -> str:
        words: List[str] | None = await self.get(self.key(user_id))

        if words is None:
            words: List[str] = []

        available_words: Set[str] = set(self._SECRET_WORDS) - set(words) or set(self._SECRET_WORDS)
        word: str = choice(list(available_words))
        words.append(word)

        if len(words) > self._GUARANTEE_UNIQUE_COUNT:
            words.pop(0)

        await self.set(self.key(user_id), words)
        return word
