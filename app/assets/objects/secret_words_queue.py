from dataclasses import field as dataclass_field
from random import choice
from typing import Dict, Any, ClassVar, List, Set
from uuid import UUID

from pydantic.dataclasses import dataclass

from app.assets.controllers.redis import RedisController
from app.assets.objects.redis import AbstractRedisObject
from app.assets.parameters import Parameters


@dataclass
class SecretWordsQueue(AbstractRedisObject):
    _FILE_PATH: ClassVar[str] = "app/assets/data/secret_words.txt"

    with open(_FILE_PATH, "r", encoding="utf-8") as file:
        _SECRET_WORDS: ClassVar[List[str]] = file.read().splitlines()

    key: ClassVar[str] = "secret_words"

    user_id: UUID
    secret_words: List[str] = dataclass_field(default_factory=list)
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

    @classmethod
    def from_json(
            cls,
            data: Dict[str, Any],
            *,
            controller: RedisController['SecretWordsQueue']
    ) -> 'SecretWordsQueue':
        return cls(**data, _controller=controller)

    def to_json(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "secret_words": self.secret_words,
            "guaranteed_unique_count": self.guaranteed_unique_count
        }

    async def get_unique_word(self) -> str:
        available_words: Set[str] = set(self._SECRET_WORDS) - set(self.secret_words) or set(self._SECRET_WORDS)
        word: str = choice(list(available_words))
        self.secret_words.append(word)

        if len(self.secret_words) > self.guaranteed_unique_count:
            self.secret_words.pop(0)

        await self.save()
        return word
