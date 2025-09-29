from uuid import UUID

from pydantic import BaseModel, Field

from app.assets.objects.single_device_game import SingleDeviceGame
from app.assets.parameters import Parameters


class SingleDeviceGameModel(BaseModel):
    game_id: UUID
    user_id: UUID
    telegram_id: int
    player_amount: int = Field(ge=Parameters.MIN_PLAYER_AMOUNT, le=Parameters.MAX_PLAYER_AMOUNT)
    secret_word: str = Field(min_length=2, max_length=32)
    spy_index: int = Field(ge=0, le=7)

    @classmethod
    def from_game(
            cls,
            game: SingleDeviceGame
    ) -> 'SingleDeviceGameModel':
        return cls(
            game_id=game.game_id,
            user_id=game.user_id,
            telegram_id=game.telegram_id,
            player_amount=game.player_amount,
            secret_word=game.secret_word,
            spy_index=game.spy_index
        )


class CreateSingleDeviceGameModel(BaseModel):
    user_id: UUID
    telegram_id: int
    player_amount: int = Field(ge=Parameters.MIN_PLAYER_AMOUNT, le=Parameters.MAX_PLAYER_AMOUNT)
