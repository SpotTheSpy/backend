from typing import Annotated, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.exceptions.already_in_game import AlreadyInGameError
from app.api.v1.exceptions.not_found import NotFoundError
from app.api.v1.models.pagination import PaginatedResult, PaginationParams
from app.api.v1.security.authenticator import Authenticator
from app.api.v1.single_device_games.models import SingleDeviceGameModel, CreateSingleDeviceGameModel
from app.assets.controllers.redis.secret_words import SecretWordsController
from app.assets.controllers.redis.single_device_games import SingleDeviceGamesController
from app.assets.objects.single_device_game import SingleDeviceGame
from app.database.models import User
from app.dependencies import single_device_games_dependency, secret_words_dependency, database_session

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
        session: Annotated[AsyncSession, Depends(database_session)],
        secret_words_controller: Annotated[SecretWordsController, Depends(secret_words_dependency)],
        games_controller: Annotated[SingleDeviceGamesController, Depends(single_device_games_dependency)]
) -> SingleDeviceGameModel:
    if not await session.scalar(select(User).filter_by(id=game_model.user_id).exists().select()):
        raise NotFoundError("User with provided UUID was not found")

    if await games_controller.players_controller.exists_player(game_model.user_id):
        raise AlreadyInGameError("You are already in game")

    secret_word: str = await secret_words_controller.get_random_secret_word(game_model.user_id)

    game: SingleDeviceGame = await games_controller.create_game(
        game_model.user_id,
        game_model.player_amount,
        secret_word
    )

    return SingleDeviceGameModel.from_game(game)


@single_device_games_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResult[SingleDeviceGameModel],
    dependencies=[Authenticator.verify_api_key()],
    name="Get all single device games"
)
async def get_single_device_games(
        pagination: Annotated[PaginationParams, Depends()],
        games_controller: Annotated[SingleDeviceGamesController, Depends(single_device_games_dependency)]
) -> PaginatedResult[SingleDeviceGameModel]:
    games: Tuple[SingleDeviceGame, ...] = await games_controller.get_games(
        pagination.limit,
        pagination.offset
    )

    return pagination.create_response(
        results=[SingleDeviceGameModel.from_game(game) for game in games],
        model=SingleDeviceGameModel
    )


@single_device_games_router.get(
    "/{game_id}",
    status_code=status.HTTP_200_OK,
    response_model=SingleDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Get single device game by UUID"
)
async def get_single_device_game_by_uuid(
        game_id: UUID,
        games_controller: Annotated[SingleDeviceGamesController, Depends(single_device_games_dependency)]
) -> SingleDeviceGameModel:
    game: SingleDeviceGame = await games_controller.get_game(game_id)

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    return SingleDeviceGameModel.from_game(game)


@single_device_games_router.get(
    "/by_user_id/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=SingleDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Get single device game by user ID"
)
async def get_single_device_game_by_user_id(
        user_id: UUID,
        games_controller: Annotated[SingleDeviceGamesController, Depends(single_device_games_dependency)]
) -> SingleDeviceGameModel:
    game: SingleDeviceGame = await games_controller.get_game_by_player(user_id)

    if game is None:
        raise NotFoundError("Game with provided user ID was not found")

    return SingleDeviceGameModel.from_game(game)


@single_device_games_router.delete(
    "/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Authenticator.verify_api_key()],
    name="Delete single device game by UUID"
)
async def delete_single_device_game_by_uuid(
        game_id: UUID,
        games_controller: Annotated[SingleDeviceGamesController, Depends(single_device_games_dependency)]
) -> None:
    if not await games_controller.exists_game(game_id):
        raise NotFoundError("Game with provided UUID was not found")

    await games_controller.remove_game(game_id)
