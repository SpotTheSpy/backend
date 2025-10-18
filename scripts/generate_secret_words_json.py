import logging
from json import dump
from typing import List, Dict, Set

from app.assets.enums.category import Category


def _get_all_secret_words() -> List[str]:
    """
    Retrieve all secret words from every category, without duplicated and in alphabetical order.

    :return: List of all secret words.
    """

    secret_words: Set[str] = set()
    categories: Set[Category] = {Category(category) for category in Category}

    for category in categories:
        filename: str = f"{category.lower()}.txt"
        with open(f"app/assets/data/secret_words/{filename}", "r", encoding="utf-8") as file:
            entries: List[str] = file.read().splitlines()
        secret_words.update(entries)

        logging.info(f"Retrieved {len(entries)} secret words from {category} category")

    return list(sorted(secret_words))


def main() -> None:
    """
    Retrieve all secret words from every category,
    and create a JSON file with all keys set to secret word tags and values as formatted titled secret words.
    """

    secret_words: List[str] = _get_all_secret_words()

    json: Dict[str, str] = {secret_word: secret_word.title().replace("_", " ") for secret_word in secret_words}
    logging.info("Converted secret words to JSON")

    with open("scripts/output/generated_secret_words.json", "w", encoding="utf-8") as file:
        dump(json, file)
    logging.info(f"Successfully dumped JSON")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
