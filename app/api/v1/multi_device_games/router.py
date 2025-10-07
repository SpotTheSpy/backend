from typing import Annotated, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.exceptions.not_found import NotFoundError
from app.api.v1.models.pagination import PaginatedResult, PaginationParams
from app.api.v1.multi_device_games.models import (
    MultiDeviceGameModel,
    CreateMultiDeviceGameModel
)
from app.api.v1.security.authenticator import Authenticator
from app.assets.controllers.redis import RedisController
from app.assets.controllers.s3.qr_codes import QRCodesController
from app.assets.objects.multi_device_active_player import MultiDeviceActivePlayer
from app.assets.objects.multi_device_game import MultiDeviceGame
from app.assets.objects.secret_words_queue import SecretWordsQueue
from app.database.models import User
from app.dependencies import multi_device_games_dependency, database_session, qr_codes_dependency, \
    secret_words_dependency, multi_device_players_dependency

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
        session: Annotated[
            AsyncSession,
            Depends(database_session)
        ],
        games_controller: Annotated[
            RedisController[MultiDeviceGame],
            Depends(multi_device_games_dependency)
        ],
        players_controller: Annotated[
            RedisController[MultiDeviceActivePlayer],
            Depends(multi_device_players_dependency)
        ],
        secret_words_controller: Annotated[
            RedisController[SecretWordsQueue],
            Depends(secret_words_dependency)
        ]
) -> MultiDeviceGameModel:
    user: User | None = await session.scalar(
        select(User)
        .filter_by(id=game_model.host_id)
    )

    if user is None:
        raise NotFoundError("User with provided UUID was not found")

    game: MultiDeviceGame = await MultiDeviceGame.host(
        user.id,
        user.telegram_id,
        user.first_name,
        game_model.player_amount,
        games_controller=games_controller,
        players_controller=players_controller,
        secret_words_controller=secret_words_controller
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
        games_controller: Annotated[
            RedisController[MultiDeviceGame],
            Depends(multi_device_games_dependency)
        ],
        players_controller: Annotated[
            RedisController[MultiDeviceActivePlayer],
            Depends(multi_device_players_dependency)
        ]
) -> PaginatedResult[MultiDeviceGameModel]:
    games: Tuple[MultiDeviceGame, ...] = await games_controller.all(
        limit=pagination.limit,
        offset=pagination.offset,
        _players_controller=players_controller
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
        games_controller: Annotated[
            RedisController[MultiDeviceGame],
            Depends(multi_device_games_dependency)
        ],
        players_controller: Annotated[
            RedisController[MultiDeviceActivePlayer],
            Depends(multi_device_players_dependency)
        ]
) -> MultiDeviceGameModel:
    game: MultiDeviceGame | None = await games_controller.get(
        game_id,
        _players_controller=players_controller
    )

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
        games_controller: Annotated[
            RedisController[MultiDeviceGame],
            Depends(multi_device_games_dependency)
        ],
        players_controller: Annotated[
            RedisController[MultiDeviceActivePlayer],
            Depends(multi_device_players_dependency)
        ]
) -> MultiDeviceGameModel:
    player: MultiDeviceActivePlayer = await players_controller.get(user_id)

    if player is None:
        raise NotFoundError("User with provided UUID was not found")

    game: MultiDeviceGame | None = await games_controller.get(
        player.game_id,
        _players_controller=players_controller
    )

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
        games_controller: Annotated[
            RedisController[MultiDeviceGame],
            Depends(multi_device_games_dependency)
        ],
        players_controller: Annotated[
            RedisController[MultiDeviceActivePlayer],
            Depends(multi_device_players_dependency)
        ],
        qr_codes_controller: Annotated[
            QRCodesController,
            Depends(qr_codes_dependency)
        ]
) -> None:
    game: MultiDeviceGame | None = await games_controller.get(
        game_id,
        _players_controller=players_controller
    )

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    await game.unhost()

    await qr_codes_controller.delete_qr_code(game_id)


@multi_device_games_router.post(
    "/{game_id}/join/{user_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=MultiDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    description="Join game by UUID"
)
async def join_game_by_uuid(
        game_id: UUID,
        user_id: UUID,
        session: Annotated[AsyncSession, Depends(database_session)],
        games_controller: Annotated[
            RedisController[MultiDeviceGame],
            Depends(multi_device_games_dependency)
        ],
        players_controller: Annotated[
            RedisController[MultiDeviceActivePlayer],
            Depends(multi_device_players_dependency)
        ]
) -> MultiDeviceGameModel:
    user: User = await session.scalar(
        select(User)
        .filter_by(id=user_id)
    )

    if user is None:
        raise NotFoundError("User with provided UUID was not found")

    game: MultiDeviceGame | None = await games_controller.get(
        game_id,
        _players_controller=players_controller
    )

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    await game.join(
        user.id,
        user.telegram_id,
        user.first_name
    )

    return MultiDeviceGameModel.from_game(game)


@multi_device_games_router.post(
    "/{game_id}/leave/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=MultiDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    description="Leave a game by UUID"
)
async def leave_game_by_uuid(
        game_id: UUID,
        user_id: UUID,
        games_controller: Annotated[
            RedisController[MultiDeviceGame],
            Depends(multi_device_games_dependency)
        ],
        players_controller: Annotated[
            RedisController[MultiDeviceActivePlayer],
            Depends(multi_device_players_dependency)
        ]
) -> MultiDeviceGameModel:
    game: MultiDeviceGame | None = await games_controller.get(
        game_id,
        _players_controller=players_controller
    )

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    await game.leave(user_id)

    return MultiDeviceGameModel.from_game(game)


@multi_device_games_router.post(
    "/{game_id}/start",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=MultiDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    description="Start game by UUID"
)
async def start_game_by_uuid(
        game_id: UUID,
        games_controller: Annotated[
            RedisController[MultiDeviceGame],
            Depends(multi_device_games_dependency)
        ],
        players_controller: Annotated[
            RedisController[MultiDeviceActivePlayer],
            Depends(multi_device_players_dependency)
        ]
) -> MultiDeviceGameModel:
    game: MultiDeviceGame | None = await games_controller.get(
        game_id,
        _players_controller=players_controller
    )

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    await game.start()

    return MultiDeviceGameModel.from_game(game)


@multi_device_games_router.post(
    "/{game_id}/restart",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=MultiDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    description="Restart game by UUID"
)
async def restart_game_by_uuid(
        game_id: UUID,
        games_controller: Annotated[
            RedisController[MultiDeviceGame],
            Depends(multi_device_games_dependency)
        ],
        players_controller: Annotated[
            RedisController[MultiDeviceActivePlayer],
            Depends(multi_device_players_dependency)
        ],
        secret_words_controller: Annotated[
            RedisController[SecretWordsQueue],
            Depends(secret_words_dependency)
        ]
) -> MultiDeviceGameModel:
    game: MultiDeviceGame | None = await games_controller.get(
        game_id,
        _players_controller=players_controller
    )

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    game: MultiDeviceGame = await MultiDeviceGame.rehost(
        game,
        secret_words_controller=secret_words_controller
    )

    return MultiDeviceGameModel.from_game(game)
