from typing import List
from uuid import UUID

from pydantic import BaseModel, Field

from app.assets.objects.multi_device_game import MultiDeviceGame
from app.assets.objects.multi_device_player import MultiDevicePlayer


class MultiDevicePlayerModel(BaseModel):
    user_id: UUID
    first_name: str = Field(min_length=2, max_length=32)

    @classmethod
    def from_player(
            cls,
            player: MultiDevicePlayer
    ) -> 'MultiDevicePlayerModel':
        return cls(
            user_id=player.user_id,
            first_name=player.first_name
        )


class MultiDeviceGameModel(BaseModel):
    game_id: UUID
    host_id: UUID
    has_started: bool
    player_amount: int = Field(ge=3, le=8)
    secret_word: str = Field(min_length=2, max_length=32)
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
            players=[MultiDevicePlayerModel.from_player(player) for player in game.players.list]
        )


class CreateMultiDeviceGameModel(BaseModel):
    host_id: UUID
    first_name: str = Field(min_length=2, max_length=32)
    player_amount: int = Field(ge=3, le=8)
