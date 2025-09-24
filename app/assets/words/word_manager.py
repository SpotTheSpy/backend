from random import choice
from typing import List


class WordManager:
    with open("app/assets/words/words.txt", "r", encoding="utf-8") as file:
        _WORDS: List[str] = file.read().splitlines()

    @classmethod
    def get_random_word(cls) -> str:
        return choice(cls._WORDS)
