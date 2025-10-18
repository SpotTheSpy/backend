from typing import Dict, Set, List

from app.assets.enums.category import Category

_secret_words: Dict[Category, Set[str]] = {}
_categories: Set[Category] = set(Category(category) for category in Category)

for category in _categories:
    filename: str = f"{category.lower()}.txt"
    with open(f"app/assets/data/secret_words/{filename}", "r", encoding="utf-8") as file:
        entries: List[str] = file.read().splitlines()
    _secret_words[category] = set(entries)


def get_secret_words(category: Category = Category.GENERAL) -> Set[str] | None:
    """
    Retrieve a set of secret word tags by word category.

    :param category: Word category.
    :return: A set of secret word tags if a category exists, otherwise None.
    """

    return _secret_words.get(category)
