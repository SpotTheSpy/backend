from random import choice
from typing import Any, ClassVar, List, Set, Self
from uuid import UUID

from pydantic import Field

from app.assets.controllers.redis import RedisController
from app.assets.objects.redis import AbstractRedisObject
from config import config

with open("app/assets/data/secret_words.txt", "r", encoding="utf-8") as file:
    _SECRET_WORDS: Set[str] = set(file.read().splitlines())


class SecretWordsQueue(AbstractRedisObject):
    """
    Represents a secret words queue in a Redis database.
    """

    key: ClassVar[str] = "secret_words"

    _SECRET_WORDS: ClassVar[Set[str]] = _SECRET_WORDS
    """
    Set of all available secret words.
    """

    user_id: UUID
    """
    User UUID.
    """

    secret_words: List[str] = Field(default_factory=list)
    """
    List of last secret words.
    """

    guaranteed_unique_count: int = config.guaranteed_unique_words_count
    """
    Count of guaranteed unique words.
    """

    @property
    def primary_key(self) -> Any:
        """
        Primary key represented by a user UUID.
        :return: User UUID.
        """

        return self.user_id

    @classmethod
    def new(
            cls,
            user_id: UUID,
            *,
            controller: RedisController[Self]
    ) -> Self | None:
        """
        Generate a new secret words queue instance using only required parameters.

        :param user_id: User UUID.
        :param controller: Secret words controller instance.
        :return: New secret words queue instance.
        """

        queue = cls(user_id=user_id)
        queue._controller = controller

        return queue

    async def get_unique_word(self) -> str:
        """
        Retrieve a new random unique word.

        Retrieves a word which has not been retrieved in last few attempts and saves new queue to Redis.

        :return: Secret word tag as a string.
        """

        available_words: Set[str] = self._SECRET_WORDS - set(self.secret_words) or self._SECRET_WORDS

        word: str = choice(list(available_words))

        self.secret_words.append(word)
        if len(self.secret_words) > self.guaranteed_unique_count:
            self.secret_words.pop(0)

        return word
