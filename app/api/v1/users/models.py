from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.assets.filters.string import LocaleStr
from app.database.models import User


class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    telegram_id: int
    first_name: str = Field(max_length=64)
    username: str | None = Field(min_length=5, max_length=32, default=None)
    locale: Annotated[str | None, LocaleStr] = None
    created_at: datetime
    updated_at: datetime | None = None

    @classmethod
    def from_database_model(
            cls,
            user: User
    ) -> 'UserModel':
        return cls.model_validate(user)


class CreateUserModel(BaseModel):
    telegram_id: int
    first_name: str = Field(max_length=64)
    username: str | None = Field(min_length=5, max_length=32, default=None)
    locale: Annotated[str | None, LocaleStr] = None


class UpdateUserModel(BaseModel):
    telegram_id: int | None = None
    first_name: str | None = Field(max_length=64, default=None)
    username: str | None = Field(min_length=5, max_length=32, default=None)
    locale: Annotated[str | None, LocaleStr] = None


class UserLocaleModel(BaseModel):
    locale: Annotated[str | None, LocaleStr] = None

    @classmethod
    def from_database_model(
            cls,
            user: User
    ) -> 'UserLocaleModel':
        return cls(locale=user.locale)


class UpdateUserLocaleModel(BaseModel):
    locale: Annotated[str | None, LocaleStr] = None
