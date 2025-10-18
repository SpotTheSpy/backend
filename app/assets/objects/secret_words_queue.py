from random import choice
from typing import Any, ClassVar, List, Set, Self
from uuid import UUID

from pydantic import Field

from app.assets.controllers.redis import RedisController
from app.assets.data.secret_words.secret_words import get_secret_words
from app.assets.enums.category import Category
from app.assets.objects.redis import AbstractRedisObject
from config import config


class SecretWordsQueue(AbstractRedisObject):
    """
    Represents a secret words queue in a Redis database.
    """

    key: ClassVar[str] = "secret_words"

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

    async def get_unique_word(
            self,
            category: Category = Category.GENERAL
    ) -> str:
        """
        Retrieve a new random unique word.

        Retrieves a word which has not been retrieved in last few attempts and saves new queue to Redis.

        :return: Secret word tag as a string.
        """

        possible_words: Set[str] = get_secret_words(category)
        available_words: Set[str] = possible_words - set(self.secret_words) or possible_words

        word: str = choice(list(available_words))

        self.secret_words.append(word)
        if len(self.secret_words) > self.guaranteed_unique_count:
            self.secret_words.pop(0)

        return word
