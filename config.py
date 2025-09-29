from typing import ClassVar

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    title: ClassVar[str] = "SpotTheSpy"

    api_key: SecretStr

    database_dsn: SecretStr
    test_database_dsn: SecretStr | None = None
    redis_dsn: SecretStr

    s3_dsn: SecretStr
    s3_region: str = "eu-central-1"
    s3_username: SecretStr
    s3_password: SecretStr
