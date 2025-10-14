from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.assets.objects.single_device_game import SingleDeviceGame
from app.assets.parameters import Parameters


class SingleDeviceGameModel(BaseModel):
    """
    Model for representing single-device game in database.

    Attributes:
        game_id: UUID.
        user_id: Host UUID.
        player_amount: Count of players.
        secret_word: Game's secret word tag.
        spy_index: Index of a game's spy (From 0 to player amount).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "game_id": "UUID",
                    "user_id": "Host UUID",
                    "player_amount": 4,
                    "secret_word": "apple",
                    "spy_index": 0
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

    player_amount: int = Field(ge=Parameters.MIN_PLAYER_AMOUNT, le=Parameters.MAX_PLAYER_AMOUNT)
    """
    Count of players.
    """

    secret_word: str = Field(min_length=2, max_length=32)
    """
    Game's secret word tag.
    """

    spy_index: int = Field(ge=0, le=7)
    """
    Index of a game's spy.
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
            spy_index=game.spy_index
        )


class CreateSingleDeviceGameModel(BaseModel):
    """
    Model for creating single-device game.

    Attributes:
        user_id: Host UUID.
        player_amount: Count of players.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "Host UUID",
                    "player_amount": 4
                }
            ]
        }
    )

    user_id: UUID
    """
    Host UUID.
    """

    player_amount: int = Field(ge=Parameters.MIN_PLAYER_AMOUNT, le=Parameters.MAX_PLAYER_AMOUNT)
    """
    Count of players.
    """
