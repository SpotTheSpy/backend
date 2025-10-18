from enum import StrEnum


class Category(StrEnum):
    """
    Category of secret words.
    """

    GENERAL = "general"
    FOOD = "food"
    NATURE = "nature"
    ANIMALS = "animals"
    PLACES = "places"
    CELEBRITIES = "celebrities"
