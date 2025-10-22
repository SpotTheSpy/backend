from typing import Annotated, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.exceptions.not_found import NotFoundError
from app.api.v1.models.pagination import PaginatedResult, PaginationParams
from app.api.v1.security.authenticator import Authenticator
from app.api.v1.single_device_games.models import SingleDeviceGameModel, CreateSingleDeviceGameModel
from app.assets.controllers.redis import RedisController
from app.assets.objects.secret_words_queue import SecretWordsQueue
from app.assets.objects.single_device_active_player import SingleDeviceActivePlayer
from app.assets.objects.single_device_game import SingleDeviceGame
from app.database.models import User
from app.dependencies import (
    single_device_games_dependency,
    secret_words_dependency,
    database_session,
    single_device_players_dependency
)

single_device_games_router = APIRouter(prefix="/single_device_games", tags=["Single_device_games"])


@single_device_games_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SingleDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Create a new single-device game"
)
async def create_single_device_game(
        game_model: CreateSingleDeviceGameModel,
        session: Annotated[
            AsyncSession,
            Depends(database_session)
        ],
        games_controller: Annotated[
            RedisController[SingleDeviceGame],
            Depends(single_device_games_dependency)
        ],
        players_controller: Annotated[
            RedisController[SingleDeviceActivePlayer],
            Depends(single_device_players_dependency)
        ],
        secret_words_controller: Annotated[
            RedisController[SecretWordsQueue],
            Depends(secret_words_dependency)
        ]
) -> SingleDeviceGameModel:
    """
    Create a new single-device game.

    Returns status code ```404``` if the user does not exist and 409 if you are already hosting a single-device game,
    otherwise returns status code ```201``` and a created game model.
    """

    if not await session.scalar(select(User).filter_by(id=game_model.user_id).exists().select()):
        raise NotFoundError("User with provided UUID was not found")

    game: SingleDeviceGame = await SingleDeviceGame.host(
        game_model.user_id,
        game_model.player_amount,
        game_model.category,
        game_model.spy_count,
        games_controller=games_controller,
        players_controller=players_controller,
        secret_words_controller=secret_words_controller
    )

    return SingleDeviceGameModel.from_game(game)


@single_device_games_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResult[SingleDeviceGameModel],
    dependencies=[Authenticator.verify_api_key()],
    name="Get all single-device games"
)
async def get_single_device_games(
        pagination: Annotated[PaginationParams, Depends()],
        games_controller: Annotated[
            RedisController[SingleDeviceGame],
            Depends(single_device_games_dependency)
        ],
        players_controller: Annotated[
            RedisController[SingleDeviceActivePlayer],
            Depends(single_device_games_dependency)
        ]
) -> PaginatedResult[SingleDeviceGameModel]:
    """
    Retrieve a list of single-device games.

    Returns a list of game models. Accepts pagination parameters.
    """

    games: Tuple[SingleDeviceGame, ...] = await games_controller.all(
        limit=pagination.limit,
        offset=pagination.offset,
        players_controller=players_controller,
        from_json_method=SingleDeviceGame.from_json_and_controllers
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
    name="Get single-device game by UUID"
)
async def get_single_device_game_by_uuid(
        game_id: UUID,
        games_controller: Annotated[
            RedisController[SingleDeviceGame],
            Depends(single_device_games_dependency)
        ],
        players_controller: Annotated[
            RedisController[SingleDeviceActivePlayer],
            Depends(single_device_games_dependency)
        ]
) -> SingleDeviceGameModel:
    """
    Retrieve a single-device game by UUID.

    Returns status code ```404``` if a game with provided UUID does not exist,
    otherwise returns status code ```200``` and a retrieved game model.
    """

    game: SingleDeviceGame = await games_controller.get(
        game_id,
        players_controller=players_controller,
        from_json_method=SingleDeviceGame.from_json_and_controllers
    )

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    return SingleDeviceGameModel.from_game(game)


@single_device_games_router.get(
    "/by_user_id/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=SingleDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Get single-device game by user ID"
)
async def get_single_device_game_by_user_id(
        user_id: UUID,
        games_controller: Annotated[
            RedisController[SingleDeviceGame],
            Depends(single_device_games_dependency)
        ],
        players_controller: Annotated[
            RedisController[SingleDeviceActivePlayer],
            Depends(single_device_players_dependency)
        ]
) -> SingleDeviceGameModel:
    """
    Retrieve a single-device game by user ID.

    Returns status code ```404``` if a user with provided UUID does not exist or user does not host a game,
    otherwise returns status code ```200``` and a retrieved game model.
    """

    player: SingleDeviceActivePlayer = await players_controller.get(user_id)

    if player is None:
        raise NotFoundError("User with provided UUID was not found")

    game: SingleDeviceGame = await games_controller.get(
        player.game_id,
        players_controller=players_controller,
        from_json_method=SingleDeviceGame.from_json_and_controllers
    )

    if game is None:
        raise NotFoundError("Game with provided user ID was not found")

    return SingleDeviceGameModel.from_game(game)


@single_device_games_router.delete(
    "/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Authenticator.verify_api_key()],
    name="Delete single-device game by UUID"
)
async def delete_single_device_game_by_uuid(
        game_id: UUID,
        games_controller: Annotated[
            RedisController[SingleDeviceGame],
            Depends(single_device_games_dependency)
        ],
        players_controller: Annotated[
            RedisController[SingleDeviceActivePlayer],
            Depends(single_device_players_dependency)
        ]
) -> None:
    """
    Delete a single-device game by user ID.

    Returns status code ```404``` if a game with provided UUID does not exist,
    otherwise returns status code ```204```.
    """

    game: SingleDeviceGame = await games_controller.get(
        game_id,
        players_controller=players_controller,
        from_json_method=SingleDeviceGame.from_json_and_controllers
    )

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    await game.unhost()


@single_device_games_router.post(
    "/{game_id}/restart",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SingleDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Restart single-device game by UUID"
)
async def restart_single_device_game_by_uuid(
        game_id: UUID,
        games_controller: Annotated[
            RedisController[SingleDeviceGame],
            Depends(single_device_games_dependency)
        ],
        players_controller: Annotated[
            RedisController[SingleDeviceActivePlayer],
            Depends(single_device_players_dependency)
        ],
        secret_words_controller: Annotated[
            RedisController[SecretWordsQueue],
            Depends(secret_words_dependency)
        ]
) -> SingleDeviceGameModel:
    """
    Restart a single-device game by UUID.

    Returns status code ```404``` if a game with provided UUID does not exist,
    otherwise returns status code ```202``` and a new game model.
    """

    game: SingleDeviceGame = await games_controller.get(
        game_id,
        players_controller=players_controller,
        from_json_method=SingleDeviceGame.from_json_and_controllers
    )

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    game: SingleDeviceGame = await game.rehost(
        game,
        secret_words_controller=secret_words_controller
    )

    return SingleDeviceGameModel.from_game(game)
