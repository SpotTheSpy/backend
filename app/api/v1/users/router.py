from typing import Annotated, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi_sa_orm_filter import FilterCore
from sqlalchemy import select, or_, update, Select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.exceptions.already_exists import AlreadyExistsError
from app.api.v1.exceptions.not_found import NotFoundError
from app.api.v1.exceptions.unique_violation import UniqueViolationError
from app.api.v1.models.pagination import PaginationParams, PaginatedResult
from app.api.v1.security.authenticator import Authenticator
from app.api.v1.users.filters import users_filters
from app.api.v1.users.models import CreateUserModel, UserModel, UserLocaleModel, UpdateUserModel, UpdateUserLocaleModel
from app.assets.controllers.redis.locales import LocalesController
from app.database.models import User
from app.dependencies import database_session, locales_dependency

users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=UserModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Create a new user"
)
async def create_user(
        user_model: CreateUserModel,
        session: Annotated[AsyncSession, Depends(database_session)],
        locales: Annotated[LocalesController, Depends(locales_dependency)]
) -> UserModel:
    if user_model.username is None:
        select_query: Select = select(User).filter_by(telegram_id=user_model.telegram_id)
    else:
        select_query: Select = select(User).filter(
            or_(
                User.telegram_id == user_model.telegram_id,
                User.username == user_model.username
            )
        )

    if await session.scalar(select_query.exists().select()):
        raise AlreadyExistsError("User with provided credentials already exists")

    user = User(
        telegram_id=user_model.telegram_id,
        first_name=user_model.first_name,
        username=user_model.username,
        locale=user_model.locale
    )
    session.add(user)
    await session.commit()

    await locales.create_locale(user.id, user.locale)

    return UserModel.from_database_model(user)


@users_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResult[UserModel],
    dependencies=[Authenticator.verify_api_key()],
    name="Get all users"
)
async def get_users(
        pagination: Annotated[PaginationParams, Depends()],
        session: Annotated[AsyncSession, Depends(database_session)],
        filters: str = Query(default=""),
) -> PaginatedResult[UserModel]:
    query: Select = pagination.apply(
        FilterCore(User, users_filters).get_query(filters)
    )

    users: Sequence[User] = (
        await session.execute(
            query
            .order_by(User.created_at)
        )
    ).unique().scalars().all()

    return pagination.create_response(
        results=[UserModel.from_database_model(user) for user in users],
        model=UserModel
    )


@users_router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Get user by UUID"
)
async def get_user_by_uuid(
        user_id: UUID,
        session: Annotated[AsyncSession, Depends(database_session)]
) -> UserModel:
    user: User = await session.scalar(
        select(User)
        .filter_by(id=user_id)
    )

    if user is None:
        raise NotFoundError("User with provided UUID was not found")

    return UserModel.from_database_model(user)


@users_router.get(
    "/telegram/{telegram_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Get user by telegram ID"
)
async def get_user_by_telegram_id(
        telegram_id: int,
        session: Annotated[AsyncSession, Depends(database_session)]
) -> UserModel:
    user: User = await session.scalar(
        select(User)
        .filter_by(telegram_id=telegram_id)
    )

    if user is None:
        raise NotFoundError("User with provided telegram ID was not found")

    return UserModel.from_database_model(user)


@users_router.put(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Authenticator.verify_api_key()],
    name="Update user by UUID"
)
async def update_user_by_uuid(
        user_id: UUID,
        user_model: UpdateUserModel,
        session: Annotated[AsyncSession, Depends(database_session)]
) -> None:
    user: User = await session.scalar(
        select(User)
        .filter_by(id=user_id)
    )

    if user is None:
        raise NotFoundError("User with provided UUID was not found")

    await session.execute(
        update(User)
        .filter_by(id=user.id)
        .values(**user_model.model_dump(exclude_unset=True))
    )

    try:
        await session.commit()
    except IntegrityError:
        raise UniqueViolationError("User with specified fields already exists")


@users_router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Authenticator.verify_api_key()],
    name="Delete user by UUID"
)
async def delete_user_by_uuid(
        user_id: UUID,
        session: Annotated[AsyncSession, Depends(database_session)]
) -> None:
    user: User = await session.scalar(
        select(User)
        .filter_by(id=user_id)
    )

    if user is None:
        raise NotFoundError("User with provided UUID was not found")

    await session.execute(
        delete(User)
        .filter_by(id=user.id)
    )
    await session.commit()


@users_router.get(
    "/locales/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserLocaleModel,
    dependencies=[Authenticator.verify_api_key()],
    name="Get user locale by UUID"
)
async def get_user_locale_by_uuid(
        user_id: UUID,
        session: Annotated[AsyncSession, Depends(database_session)],
        locales: Annotated[LocalesController, Depends(locales_dependency)]
) -> UserLocaleModel:
    locale: str = await locales.get_locale(user_id)

    if locale is not None:
        return UserLocaleModel(locale=locale)

    user: User = await session.scalar(
        select(User)
        .filter_by(id=user_id)
    )

    if user is None:
        raise NotFoundError("User with provided UUID was not found")

    await locales.create_locale(user.id, user.locale)

    return UserLocaleModel.from_database_model(user)


@users_router.put(
    "/locales/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Authenticator.verify_api_key()],
    name="Update user locale by UUID"
)
async def update_user_locale_by_telegram_id(
        user_id: UUID,
        locale_model: UpdateUserLocaleModel,
        session: Annotated[AsyncSession, Depends(database_session)],
        locales: Annotated[LocalesController, Depends(locales_dependency)]
) -> None:
    user: User = await session.scalar(
        select(User)
        .filter_by(id=user_id)
    )

    if user is None:
        raise NotFoundError("User with provided UUID was not found")

    await session.execute(
        update(User)
        .filter_by(id=user.id)
        .values(locale=locale_model.locale)
    )
    await session.commit()

    await locales.create_locale(user.id, locale_model.locale)
