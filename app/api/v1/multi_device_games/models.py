from typing import List
from uuid import UUID

from pydantic import BaseModel, Field

from app.assets.enums.player_role import PlayerRole
from app.assets.objects.multi_device_game import MultiDeviceGame
from app.assets.objects.multi_device_player import MultiDevicePlayer
from app.assets.parameters import Parameters


class MultiDevicePlayerModel(BaseModel):
    user_id: UUID
    telegram_id: int
    first_name: str = Field(max_length=32)
    role: PlayerRole | None = None

    @classmethod
    def from_player(
            cls,
            player: MultiDevicePlayer
    ) -> 'MultiDevicePlayerModel':
        return cls(
            user_id=player.user_id,
            telegram_id=player.telegram_id,
            first_name=player.first_name,
            role=player.role
        )


class MultiDeviceGameModel(BaseModel):
    game_id: UUID
    host_id: UUID
    has_started: bool
    player_amount: int = Field(ge=Parameters.MIN_PLAYER_AMOUNT, le=Parameters.MAX_PLAYER_AMOUNT)
    secret_word: str = Field(min_length=2, max_length=32)
    qr_code_url: str | None = Field(min_length=16, default=None)
    players: List[MultiDevicePlayerModel]

    @classmethod
    def from_game(
            cls,
            game: MultiDeviceGame
    ) -> 'MultiDeviceGameModel':
        return cls(
            game_id=game.game_id,
            host_id=game.host_id,
            has_started=game.has_started,
            player_amount=game.player_amount,
            secret_word=game.secret_word,
            qr_code_url=game.qr_code_url,
            players=[MultiDevicePlayerModel.from_player(player) for player in game.players.list]
        )


class CreateMultiDeviceGameModel(BaseModel):
    host_id: UUID
    player_amount: int = Field(ge=Parameters.MIN_PLAYER_AMOUNT, le=Parameters.MAX_PLAYER_AMOUNT)


class SetGameURLModel(BaseModel):
    url: str = Field(min_length=16)
