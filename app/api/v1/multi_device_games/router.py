from typing import Annotated, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from app.api.v1.exceptions.already_in_game import AlreadyInGameError
from app.api.v1.exceptions.not_found import NotFoundError
from app.api.v1.models.pagination import PaginatedResult, PaginationParams
from app.api.v1.multi_device_games.models import MultiDeviceGameModel, CreateMultiDeviceGameModel
from app.api.v1.security.authenticator import Authenticator
from app.assets.controllers.redis.multi_device_games import MultiDeviceGamesController
from app.assets.objects.multi_device_game import MultiDeviceGame
from app.dependencies import multi_device_games_dependency

multi_device_games_router = APIRouter(prefix="/multi_device_games", tags=["Multi_device_games"])


@multi_device_games_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=MultiDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    description="Create a multi device game"
)
async def create_multi_device_game(
        game_model: CreateMultiDeviceGameModel,
        games_controller: Annotated[MultiDeviceGamesController, Depends(multi_device_games_dependency)]
) -> MultiDeviceGameModel:
    if await games_controller.players_controller.exists_player(game_model.user_id):
        raise AlreadyInGameError("You are already in game")

    game: MultiDeviceGame = await games_controller.create_game(
        game_model.user_id,
        game_model.telegram_id,
        game_model.player_amount
    )

    return MultiDeviceGameModel.from_game(game)


@multi_device_games_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResult[MultiDeviceGameModel],
    dependencies=[Authenticator.verify_api_key()],
    name="Get all multi device games"
)
async def get_multi_device_games(
        pagination: Annotated[PaginationParams, Depends()],
        games_controller: Annotated[MultiDeviceGamesController, Depends(multi_device_games_dependency)]
) -> PaginatedResult[MultiDeviceGameModel]:
    games: Tuple[MultiDeviceGame, ...] = await games_controller.get_games(
        pagination.limit,
        pagination.offset
    )

    return pagination.create_response(
        results=[MultiDeviceGameModel.from_game(game) for game in games],
        model=MultiDeviceGameModel
    )


@multi_device_games_router.get(
    "/{game_id}",
    status_code=status.HTTP_200_OK,
    response_model=MultiDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Get multi device game by UUID"
)
async def get_multi_device_game_by_uuid(
        game_id: UUID,
        games_controller: Annotated[MultiDeviceGamesController, Depends(multi_device_games_dependency)]
) -> MultiDeviceGameModel:
    game: MultiDeviceGame = await games_controller.get_game(game_id)

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    return MultiDeviceGameModel.from_game(game)


@multi_device_games_router.get(
    "/by_user_id/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=MultiDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Get multi device game by user ID"
)
async def get_multi_device_game_by_user_id(
        user_id: UUID,
        games_controller: Annotated[MultiDeviceGamesController, Depends(multi_device_games_dependency)]
) -> MultiDeviceGameModel:
    game: MultiDeviceGame = await games_controller.get_game_by_player(user_id)

    if game is None:
        raise NotFoundError("Game with provided user ID was not found")

    return MultiDeviceGameModel.from_game(game)


@multi_device_games_router.delete(
    "/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Authenticator.verify_api_key()],
    name="Delete multi device game by UUID"
)
async def delete_multi_device_game_by_uuid(
        game_id: UUID,
        games_controller: Annotated[MultiDeviceGamesController, Depends(multi_device_games_dependency)]
) -> None:
    if not await games_controller.exists_game(game_id):
        raise NotFoundError("Game with provided UUID was not found")

    await games_controller.remove_game(game_id)
