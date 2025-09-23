from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from app.api.v1.exceptions.already_in_game import AlreadyInGameError
from app.api.v1.security.authenticator import Authenticator
from app.api.v1.single_device_games.models import SingleDeviceGameModel, CreateSingleDeviceGameModel
from app.assets.controllers.redis.single_device_games import SingleDeviceGamesController
from app.assets.objects.single_device_game import SingleDeviceGame
from app.dependencies import single_games_dependency

single_device_games_router = APIRouter(prefix="/single_device_games", tags=["Single_device_games"])


@single_device_games_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SingleDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    description="Create a single device game"
)
async def create_single_device_game(
        game_model: CreateSingleDeviceGameModel,
        games_controller: Annotated[SingleDeviceGamesController, Depends(single_games_dependency)]
) -> SingleDeviceGameModel:
    if await games_controller.players_controller.exists_player(game_model.user_id):
        raise AlreadyInGameError("You are already in game")

    game: SingleDeviceGame = await games_controller.create_game(
        game_model.user_id,
        game_model.telegram_id,
        game_model.player_amount,
        game_model.secret_word
    )

    return SingleDeviceGameModel.from_game(game)
