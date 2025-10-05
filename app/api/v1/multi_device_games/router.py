from typing import Annotated, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.exceptions.already_in_game import AlreadyInGameError
from app.api.v1.exceptions.game_has_already_started import GameHasAlreadyStartedError
from app.api.v1.exceptions.invalid_player_amount import InvalidPlayerAmountError
from app.api.v1.exceptions.not_found import NotFoundError
from app.api.v1.exceptions.not_in_game import NotInGameError
from app.api.v1.models.pagination import PaginatedResult, PaginationParams
from app.api.v1.multi_device_games.models import (
    MultiDeviceGameModel,
    CreateMultiDeviceGameModel,
    SetGameURLModel
)
from app.api.v1.security.authenticator import Authenticator
from app.assets.controllers.redis.multi_device_games import MultiDeviceGamesController
from app.assets.controllers.redis.secret_words import SecretWordsController
from app.assets.controllers.s3.qr_codes import QRCodesController
from app.assets.objects.multi_device_game import MultiDeviceGame
from app.assets.objects.multi_device_player import MultiDevicePlayer
from app.assets.parameters import Parameters
from app.database.models import User
from app.dependencies import multi_device_games_dependency, database_session, qr_codes_dependency, \
    secret_words_dependency

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
        session: Annotated[AsyncSession, Depends(database_session)],
        secret_words_controller: Annotated[SecretWordsController, Depends(secret_words_dependency)],
        games_controller: Annotated[MultiDeviceGamesController, Depends(multi_device_games_dependency)]
) -> MultiDeviceGameModel:
    user: User | None = await session.scalar(
        select(User)
        .filter_by(id=game_model.host_id)
    )

    if user is None:
        raise NotFoundError("User with provided UUID was not found")

    if await games_controller.players_controller.exists_player(game_model.host_id):
        raise AlreadyInGameError("You are already in game")

    secret_word: str = await secret_words_controller.get_random_secret_word(game_model.host_id)

    game: MultiDeviceGame = await games_controller.create_game(
        user.id,
        user.telegram_id,
        user.first_name,
        game_model.player_amount,
        secret_word,
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
        games_controller: Annotated[MultiDeviceGamesController, Depends(multi_device_games_dependency)],
        qr_codes_controller: Annotated[QRCodesController, Depends(qr_codes_dependency)]
) -> None:
    if not await games_controller.exists_game(game_id):
        raise NotFoundError("Game with provided UUID was not found")

    await games_controller.remove_game(game_id)
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
        games_controller: Annotated[MultiDeviceGamesController, Depends(multi_device_games_dependency)]
) -> MultiDeviceGameModel:
    user: User = await session.scalar(
        select(User)
        .filter_by(id=user_id)
    )

    if user is None:
        raise NotFoundError("User with provided UUID was not found")

    game: MultiDeviceGame | None = await games_controller.get_game(game_id)

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")
    if game.has_started:
        raise GameHasAlreadyStartedError("Game has already started")
    if game.players.exists(user_id):
        raise AlreadyInGameError("You are already in game")
    if game.player_amount >= Parameters.MAX_PLAYER_AMOUNT:
        raise InvalidPlayerAmountError("Game has too many players")

    game.players.add(
        MultiDevicePlayer.new(
            user_id=user.id,
            telegram_id=user.telegram_id,
            first_name=user.first_name,
            game=game
        )
    )

    await game.save()

    await games_controller.players_controller.create_player(
        user_id=user.id,
        game_id=game.game_id
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
        games_controller: Annotated[MultiDeviceGamesController, Depends(multi_device_games_dependency)]
) -> MultiDeviceGameModel:
    game: MultiDeviceGame | None = await games_controller.get_game(game_id)

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")
    if game.has_started:
        raise GameHasAlreadyStartedError("Game has already started")
    if not game.players.exists(user_id):
        raise NotInGameError("You are not in game")

    game.players.remove(user_id)
    await game.save()

    await games_controller.players_controller.remove_player(user_id)

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
        games_controller: Annotated[MultiDeviceGamesController, Depends(multi_device_games_dependency)]
) -> MultiDeviceGameModel:
    game: MultiDeviceGame | None = await games_controller.get_game(game_id)

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")
    if game.has_started:
        raise GameHasAlreadyStartedError("Game has already started")
    if game.players.size < Parameters.MIN_PLAYER_AMOUNT or game.players.size > Parameters.MAX_PLAYER_AMOUNT:
        raise InvalidPlayerAmountError("Game has either too many players or too few players")

    game.start()
    await game.save()

    return MultiDeviceGameModel.from_game(game)


@multi_device_games_router.post(
    "/{game_id}/url",
    status_code=status.HTTP_201_CREATED,
    response_model=MultiDeviceGameModel,
    dependencies=[Authenticator.verify_api_key()],
    description="Set game url by UUID"
)
async def set_game_url_by_uuid(
        game_id: UUID,
        url_model: SetGameURLModel,
        games_controller: Annotated[MultiDeviceGamesController, Depends(multi_device_games_dependency)],
        qr_codes_controller: Annotated[QRCodesController, Depends(qr_codes_dependency)]
) -> MultiDeviceGameModel:
    game: MultiDeviceGame = await games_controller.get_game(game_id)

    if game is None:
        raise NotFoundError("Game with provided UUID was not found")

    await qr_codes_controller.upload_qr_code(game.game_id, url_model.url)
    game.qr_code_url = await qr_codes_controller.get_qr_code_url(game.game_id)

    await game.save()
    return MultiDeviceGameModel.from_game(game)
