from random import choice
from typing import Any, ClassVar, List, Set
from uuid import UUID

from pydantic import Field

from app.assets.controllers.redis import RedisController
from app.assets.objects.redis import AbstractRedisObject
from app.assets.parameters import Parameters

with open("app/assets/data/secret_words.txt", "r", encoding="utf-8") as file:
    _SECRET_WORDS: Set[str] = set(file.read().splitlines())


class SecretWordsQueue(AbstractRedisObject):
    key: ClassVar[str] = "secret_words"
    _SECRET_WORDS: ClassVar[Set[str]] = _SECRET_WORDS

    user_id: UUID
    secret_words: List[str] = Field(default_factory=list)
    guaranteed_unique_count: int = Parameters.GUARANTEED_UNIQUE_WORDS_COUNT

    @property
    def primary_key(self) -> Any:
        return self.user_id

    @classmethod
    def new(
            cls,
            user_id: UUID,
            *,
            controller: RedisController['SecretWordsQueue']
    ) -> 'SecretWordsQueue':
        queue = cls(user_id=user_id)
        queue._controller = controller

        return queue

    async def get_unique_word(self) -> str:
        available_words: Set[str] = self._SECRET_WORDS - set(self.secret_words) or self._SECRET_WORDS

        word: str = choice(list(available_words))

        self.secret_words.append(word)
        if len(self.secret_words) > self.guaranteed_unique_count:
            self.secret_words.pop(0)

        return word
