from random import choice
from typing import List


class SecretWordsController:
    _FILE_PATH: str = "app/assets/data/secret_words.txt"

    with open(_FILE_PATH, "r", encoding="utf-8") as file:
        _SECRET_WORDS: List[str] = file.read().splitlines()

    @classmethod
    def get_random_secret_word(cls) -> str:
        return choice(cls._SECRET_WORDS)
