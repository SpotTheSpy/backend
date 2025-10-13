from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.assets.filters.string import LocaleStr
from app.database.models import User


class UserModel(BaseModel):
    """
    Model for representing user in database.

    Attributes:
        id: UUID.
        telegram_id: User's telegram ID.
        first_name: First name from telegram.
        username: Username from telegram.
        locale: User's locale. Used to localize telegram responses.
        created_at: User's creation date.
        updated_at: User's last update date.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "UUID",
                    "telegram_id": 123456789,
                    "first_name": "John Smith",
                    "username": "john123",
                    "locale": "en",
                    "created_at": "Creation date",
                    "updated_at": "Last update date"
                }
            ]
        }
    )

    id: UUID
    """
    UUID.
    """

    telegram_id: int
    """
    User's telegram ID.
    """

    first_name: str = Field(max_length=64)
    """
    First name from telegram.
    """

    username: str | None = Field(min_length=5, max_length=32, default=None)
    """
    Username from telegram.
    """

    locale: Annotated[str | None, LocaleStr] = None
    """
    User's locale. Used to localize telegram responses.
    '"""

    created_at: datetime
    """
    User's creation date.
    """

    updated_at: datetime | None = None
    """
    User's last update date.
    """

    @classmethod
    def from_database_model(
            cls,
            user: User
    ) -> Self:
        """
        Retrieve model from database object.

        :param user: Database user object.
        :return: Retrieved model instance.
        """

        return cls.model_validate(user)


class CreateUserModel(BaseModel):
    """
    Model for creating user.

    Attributes:
        telegram_id: User's telegram ID.
        first_name: First name from telegram (Max length is 64 symbols).
        username: Username from telegram (Nullable, min length is 5 symbols, max length is 32 symbols).
        locale: User's locale (Nullable, must be a default locale format). Used to localize telegram responses.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "telegram_id": 123456789,
                    "first_name": "John Smith",
                    "username": "john123",
                    "locale": "en"
                }
            ]
        }
    )

    telegram_id: int
    """
    User's telegram ID.
    """

    first_name: str = Field(max_length=64)
    """
    First name from telegram.
    """

    username: str | None = Field(min_length=5, max_length=32, default=None)
    """
    Username from telegram.
    """

    locale: Annotated[str | None, LocaleStr] = None
    """
    User's locale. Used to localize telegram responses.
    """


class UpdateUserModel(BaseModel):
    """
    Model for updating user.

    Attributes:
        telegram_id: User's telegram ID.
        first_name: First name from telegram (Max length is 64 symbols).
        username: Username from telegram (Min length is 5 symbols, max length is 32 symbols).
        locale: User's locale (Must be a default locale format). Used to localize telegram responses.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "telegram_id": 123456789,
                    "first_name": "John Smith",
                    "username": "john123",
                    "locale": "en"
                }
            ]
        }
    )

    telegram_id: int | None = None
    """
    User's telegram ID.
    """

    first_name: str | None = Field(max_length=64, default=None)
    """
    First name from telegram.
    """

    username: str | None = Field(min_length=5, max_length=32, default=None)
    """
    Username from telegram.
    """

    locale: Annotated[str | None, LocaleStr] = None
    """
    User's locale. Used to localize telegram responses.
    """
