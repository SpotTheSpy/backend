from typing import List, Self
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.assets.enums.player_role import PlayerRole
from app.assets.objects.multi_device_game import MultiDeviceGame
from app.assets.objects.multi_device_player import MultiDevicePlayer
from config import config


class MultiDevicePlayerModel(BaseModel):
    """
    Model for representing player of a multi-device game.

    Attributes:
        user_id: UUID.
        telegram_id: User's telegram ID.
        first_name: First name from telegram.
        role: User's role in game.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "UUID",
                    "telegram_id": 123456789,
                    "first_name": "John Smith",
                    "role": PlayerRole.CITIZEN
                }
            ]
        }
    )

    user_id: UUID
    """
    UUID.
    """

    telegram_id: int
    """
    User's telegram ID.
    """

    first_name: str = Field(max_length=32)
    """
    First name from telegram.
    """

    role: PlayerRole | None = None
    """
    User's role in game.
    """

    @classmethod
    def from_player(
            cls,
            player: MultiDevicePlayer
    ) -> Self:
        """
        Retrieve model from multi-device player object.

        :param player: Multi-device player object.
        :return: Retrieved model instance.
        """

        return cls(
            user_id=player.user_id,
            telegram_id=player.telegram_id,
            first_name=player.first_name,
            role=player.role
        )


class MultiDeviceGameModel(BaseModel):
    """
    Model for representing multi-device game in database.

    Attributes:
        game_id: UUID.
        host_id: Host UUID.
        has_started: Is the game started.
        player_amount: Count of max players who can join.
        secret_word: Game's secret word tag.
        qr_code_url: QR code URL for a direct image download.
        players: List of game players.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "game_id": "UUID",
                    "host_id": "Host UUID",
                    "has_started": True,
                    "player_amount": 4,
                    "secret_word": "apple",
                    "qr_code_url": "https://example.com/qr.jpg",
                    "players": [
                        {
                            "user_id": "UUID",
                            "telegram_id": 123456789,
                            "first_name": "John Smith",
                            "role": PlayerRole.CITIZEN
                        }
                    ]
                }
            ]
        }
    )

    game_id: UUID
    """
    UUID.
    """

    host_id: UUID
    """
    Host UUID.
    """

    has_started: bool
    """
    Is the game started.
    """

    player_amount: int = Field(ge=config.min_player_amount, le=config.max_player_amount)
    """
    Count of max players who can join.
    """

    secret_word: str = Field(min_length=2, max_length=32)
    """
    Game's secret word tag.
    """

    qr_code_url: str | None = Field(min_length=16, default=None)
    """
    QR code URL for a direct image download.
    """

    players: List[MultiDevicePlayerModel]
    """
    List of game players.
    """

    @classmethod
    def from_game(
            cls,
            game: MultiDeviceGame
    ) -> Self:
        """
        Retrieve model from multi-device game object.

        :param game: Multi-device game object.
        :return: Retrieved model instance.
        """

        return cls(
            game_id=game.game_id,
            host_id=game.host_id,
            has_started=game.has_started,
            player_amount=game.player_amount,
            secret_word=game.secret_word,
            qr_code_url=game.qr_code_url,
            players=[MultiDevicePlayerModel.from_player(player) for player in game.players.values()]
        )


class CreateMultiDeviceGameModel(BaseModel):
    """
    Model for creating multi-device game.

    Attributes:
        host_id: Host UUID.
        player_amount: Count of max players who can join.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "host_id": "Host UUID",
                    "player_amount": 4
                }
            ]
        }
    )

    host_id: UUID
    """
    Host UUID.
    """

    player_amount: int = Field(ge=config.min_player_amount, le=config.max_player_amount)
    """
    Count of max players who can join.
    """
