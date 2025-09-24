from uuid import UUID

from pydantic import BaseModel, Field

from app.assets.objects.single_device_game import SingleDeviceGame


class SingleDeviceGameModel(BaseModel):
    game_id: UUID
    user_id: UUID
    telegram_id: int
    secret_word: str = Field(min_length=2, max_length=32)
    player_amount: int = Field(ge=3, le=8)
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
            secret_word=game.secret_word,
            player_amount=game.player_amount,
            spy_index=game.spy_index
        )


class CreateSingleDeviceGameModel(BaseModel):
    user_id: UUID
    telegram_id: int
    player_amount: int = Field(ge=3, le=8)
