import logging
from json import dump
from typing import List, Dict

__FILE_PATH: str = "app/assets/data/{file_name}"


def main() -> None:
    file_name: str = input("Enter file name: ")
    if not file_name:
        file_name = "secret_words"
    file_name = file_name.removesuffix(".txt")

    with open(__FILE_PATH.format(file_name=f"{file_name}.txt"), "r", encoding="utf-8") as file:
        secret_words: List[str] = file.read().splitlines()
    logging.info(f"Exported {len(secret_words)} secret words")

    json: Dict[str, str] = {secret_word: secret_word.title().replace("_", " ") for secret_word in secret_words}
    logging.info("Converted secret words to JSON")

    with open(__FILE_PATH.format(file_name=f"{file_name}.json"), "w", encoding="utf-8") as file:
        dump(json, file)
    logging.info(f"Dumped JSON to file at {__FILE_PATH.format(file_name=f"{file_name}.json")}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
