from random import choice
from typing import Any, ClassVar, List, Set
from uuid import UUID

from pydantic import Field

from app.assets.controllers.redis import RedisController
from app.assets.objects.redis import AbstractRedisObject
from app.assets.parameters import Parameters


class SecretWordsQueue(AbstractRedisObject):
    _FILE_PATH: ClassVar[str] = "app/assets/data/secret_words.txt"

    with open(_FILE_PATH, "r", encoding="utf-8") as file:
        _SECRET_WORDS: ClassVar[Set[str]] = set(file.read().splitlines())

    key: ClassVar[str] = "secret_words"

    user_id: UUID
    secret_words: List[str] = Field(default_factory=list)
    guaranteed_unique_count: int | None = None

    def __post_init__(self) -> None:
        if self.guaranteed_unique_count is None:
            self.guaranteed_unique_count = Parameters.GUARANTEED_UNIQUE_WORDS_COUNT

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
        return cls(
            user_id=user_id,
            _controller=controller
        )

    async def get_unique_word(self) -> str:
        available_words: Set[str] = self._SECRET_WORDS - set(self.secret_words) or self._SECRET_WORDS

        word: str = choice(list(available_words))

        self.secret_words.append(word)
        if len(self.secret_words) > self.guaranteed_unique_count:
            self.secret_words.pop(0)

        return word
