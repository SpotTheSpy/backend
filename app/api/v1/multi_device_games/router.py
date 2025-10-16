from typing import Annotated, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks
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
from app.assets.controllers.s3 import S3Controller
from app.assets.objects.multi_device_active_player import MultiDeviceActivePlayer
from app.assets.objects.multi_device_game import MultiDeviceGame
from app.assets.objects.qr_code import QRCode
from app.assets.objects.secret_words_queue import SecretWordsQueue
from app.database.models import User
from app.dependencies import (
    multi_device_games_dependency,
    database_session,
    secret_words_dependency,
    multi_device_players_dependency,
    qr_codes_dependency
)

multi_device_games_router = APIRouter(prefix="/multi_device_games", tags=["Multi_device_games"])


@multi_device_games_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=MultiDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Create a multi-device game"
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
    """
    Create a new multi-device game.

    Returns status code ```404``` if the user does not exist and 409 if you are already hosting a multi-device game,
    otherwise returns status code ```201``` and a created game model.
    """

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
    name="Get all multi-device games"
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
    """
    Retrieve a list of multi-device games.

    Returns a list of game models. Accepts pagination parameters.
    """

    games: Tuple[MultiDeviceGame, ...] = await games_controller.all(
        limit=pagination.limit,
        offset=pagination.offset,
        players_controller=players_controller,
        from_json_method=MultiDeviceGame.from_json_and_controllers
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
    name="Get multi-device game by UUID"
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
    """
    Retrieve a multi-device game by UUID.

    Returns status code ```404``` if a game with provided UUID does not exist,
    otherwise returns status code ```200``` and a retrieved game model.
    """

    game: MultiDeviceGame | None = await games_controller.get(
        game_id,
        players_controller=players_controller,
        from_json_method=MultiDeviceGame.from_json_and_controllers
    )

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    return MultiDeviceGameModel.from_game(game)


@multi_device_games_router.get(
    "/by_user_id/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=MultiDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Get multi-device game by user ID"
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
    """
    Retrieve a multi-device game by user ID.

    Returns status code ```404``` if a user with provided UUID does not exist or user does not host a game,
    otherwise returns status code ```200``` and a retrieved game model.
    """

    player: MultiDeviceActivePlayer = await players_controller.get(user_id)

    if player is None:
        raise NotFoundError("User with provided UUID was not found")

    game: MultiDeviceGame | None = await games_controller.get(
        player.game_id,
        players_controller=players_controller,
        from_json_method=MultiDeviceGame.from_json_and_controllers
    )

    if game is None:
        raise NotFoundError("Game with provided user ID was not found")

    return MultiDeviceGameModel.from_game(game)


@multi_device_games_router.delete(
    "/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Authenticator.verify_api_key()],
    name="Delete multi-device game by UUID"
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
            S3Controller[QRCode],
            Depends(qr_codes_dependency)
        ],
        background_tasks: BackgroundTasks
) -> None:
    """
    Delete a multi-device game by user ID.

    Returns status code ```404``` if a game with provided UUID does not exist,
    otherwise returns status code ```204```.
    """

    game: MultiDeviceGame | None = await games_controller.get(
        game_id,
        players_controller=players_controller,
        from_json_method=MultiDeviceGame.from_json_and_controllers
    )

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    background_tasks.add_task(
        qr_codes_controller.remove,
        QRCode.new(
            str(game.game_id),
            b""
        ).primary_key
    )

    await game.unhost()


@multi_device_games_router.post(
    "/{game_id}/join/{user_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=MultiDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Join multi-device game by UUID"
)
async def join_multi_device_game_by_uuid(
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
    """
    Join a multi-device game by game ID and user ID.

    Returns status code ```404``` if a user or game with provided UUID does not exist,
    ```400``` if a game has already started,
    ```409``` if a user is already in game
    and ```406``` if a game has too many players,
    otherwise returns status code ```202``` and a game model with a new player.
    """

    user: User = await session.scalar(
        select(User)
        .filter_by(id=user_id)
    )

    if user is None:
        raise NotFoundError("User with provided UUID was not found")

    game: MultiDeviceGame | None = await games_controller.get(
        game_id,
        players_controller=players_controller,
        from_json_method=MultiDeviceGame.from_json_and_controllers
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
    "/leave/{user_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=MultiDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Leave multi-device game by UUID"
)
async def leave_multi_device_game_by_uuid(
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
    """
    Leave a multi-device game by game ID and user ID.

    Returns status code ```404``` if a user with provided UUID does not exist or user does not host a game
    and ```409``` if a user is not in game,
    otherwise returns status code ```202``` and a game model without a left player.
    """

    player: MultiDeviceActivePlayer = await players_controller.get(user_id)

    if player is None:
        raise NotFoundError("User with provided UUID was not found")

    game: MultiDeviceGame | None = await games_controller.get(
        player.game_id,
        players_controller=players_controller,
        from_json_method=MultiDeviceGame.from_json_and_controllers
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
    name="Start multi device game by UUID"
)
async def start_multi_device_game_by_uuid(
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
            S3Controller[QRCode],
            Depends(qr_codes_dependency)
        ],
        background_tasks: BackgroundTasks
) -> MultiDeviceGameModel:
    """
    Start a multi-device game by game ID.

    Returns status code ```404``` if a game with provided UUID does not exist,
    ```400``` if a game has already started
    and ```406``` if a game has too few players,
    otherwise returns status code ```202``` and a started game model.
    """

    game: MultiDeviceGame | None = await games_controller.get(
        game_id,
        players_controller=players_controller,
        from_json_method=MultiDeviceGame.from_json_and_controllers
    )

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    await game.start()

    background_tasks.add_task(
        qr_codes_controller.remove,
        QRCode.new(
            str(game.game_id),
            b""
        ).primary_key
    )

    return MultiDeviceGameModel.from_game(game)


@multi_device_games_router.post(
    "/{game_id}/restart",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=MultiDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Restart multi device game by UUID"
)
async def restart_multi_device_game_by_uuid(
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
    """
    Restart a multi-device game by game ID.

    Returns status code ```404``` if a game with provided UUID does not exist
    and ```409``` if a user is already in game,
    otherwise returns status code ```202``` and a new game model.
    """

    game: MultiDeviceGame | None = await games_controller.get(
        game_id,
        players_controller=players_controller,
        from_json_method=MultiDeviceGame.from_json_and_controllers
    )

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    game: MultiDeviceGame = await MultiDeviceGame.rehost(
        game,
        secret_words_controller=secret_words_controller
    )

    return MultiDeviceGameModel.from_game(game)


@multi_device_games_router.post(
    "/{game_id}/qr_code",
    status_code=status.HTTP_201_CREATED,
    response_model=MultiDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Generate multi device game QR code by UUID"
)
async def generate_qr_code_by_uuid(
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
            S3Controller[QRCode],
            Depends(qr_codes_dependency)
        ]
) -> MultiDeviceGameModel:
    """
    Generate a QR-Code for a multi-device game by game ID.

    Returns status code ```404``` if a game with provided UUID does not exist,
    otherwise returns status code ```201``` and a game model with a valid QR-Code URL.
    """

    game: MultiDeviceGame | None = await games_controller.get(
        game_id,
        players_controller=players_controller,
        from_json_method=MultiDeviceGame.from_json_and_controllers
    )

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    await game.generate_qr_code(qr_codes_controller=qr_codes_controller)

    return MultiDeviceGameModel.from_game(game)
