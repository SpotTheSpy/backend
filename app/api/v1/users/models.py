from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.database.models import User


class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    telegram_id: int
    first_name: str = Field(min_length=1, max_length=64)
    username: str = Field(min_length=5, max_length=32)
    locale: str | None = Field(min_length=2, max_length=8)
    created_at: datetime
    updated_at: datetime | None = None

    @classmethod
    def from_database_model(
            cls,
            user: User
    ) -> 'UserModel':
        return cls.model_validate(user)


class UserLocaleModel(BaseModel):
    locale: str | None = Field(min_length=2, max_length=8)

    @classmethod
    def from_database_model(
            cls,
            user: User
    ) -> 'UserLocaleModel':
        return cls(locale=user.locale)


class CreateUserModel(BaseModel):
    telegram_id: int
    first_name: str = Field(min_length=1, max_length=64)
    username: str = Field(min_length=5, max_length=32)
    locale: str | None = Field(min_length=2, max_length=8, default=None)
