from typing import Self, Tuple
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.assets.enums.category import Category
from app.assets.enums.spy_count import SpyCount
from app.assets.objects.single_device_game import SingleDeviceGame
from config import config


class SingleDeviceGameModel(BaseModel):
    """
    Model for representing single-device game in database.

    Attributes:
        game_id: UUID.
        user_id: Host UUID.
        player_amount: Count of players.
        secret_word: Game's secret word tag.
        category: Secret word category.
        spy_indices: Indices of spies games.
        spy_count: Count of spies.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "game_id": "UUID",
                    "user_id": "Host UUID",
                    "player_amount": 4,
                    "secret_word": "apple",
                    "category": "food",
                    "spy_indices": (1, 2),
                    "spy_count": "double"
                }
            ]
        }
    )

    game_id: UUID
    """
    UUID.
    """

    user_id: UUID
    """
    Host UUID.
    """

    player_amount: int = Field(ge=config.min_player_amount, le=config.max_player_amount)
    """
    Count of players.
    """

    secret_word: str = Field(min_length=2, max_length=32)
    """
    Game's secret word tag.
    """

    category: Category = Field(min_length=2, max_length=32)
    """
    Secret word category.
    """

    spy_indices: Tuple[int, ...]
    """
    Indices of spies in game.
    """

    spy_count: SpyCount = Field(min_length=2, max_length=32)
    """
    Count of spies.
    """

    @classmethod
    def from_game(
            cls,
            game: SingleDeviceGame
    ) -> Self:
        """
        Retrieve model from single-device game object.

        :param game: Single-device game object.
        :return: Retrieved model instance.
        """

        return cls(
            game_id=game.game_id,
            user_id=game.user_id,
            player_amount=game.player_amount,
            secret_word=game.secret_word,
            category=game.category,
            spy_indices=game.spy_indices,
            spy_count=game.spy_count
        )


class CreateSingleDeviceGameModel(BaseModel):
    """
    Model for creating single-device game.

    Attributes:
        user_id: Host UUID.
        player_amount: Count of players.
        category: Secret word category.
        spy_count: Count of spies.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "Host UUID",
                    "player_amount": 4,
                    "category": Category.GENERAL,
                    "spy_count": SpyCount.SINGLE
                }
            ]
        }
    )

    user_id: UUID
    """
    Host UUID.
    """

    player_amount: int = Field(ge=config.min_player_amount, le=config.max_player_amount)
    """
    Count of players.
    """

    category: Category = Field(min_length=2, max_length=32, default=Category.GENERAL)
    """
    Secret word category.
    """

    spy_count: SpyCount = Field(min_length=2, max_length=32, default=SpyCount.SINGLE)
    """
    Count of spies.
    """
