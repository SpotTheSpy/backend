from typing import ClassVar

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """
    Main config class.

    Provides access credentials for all Back-End services, and an API Key for endpoint access.
    """

    TITLE: ClassVar[str] = "SpotTheSpy"
    """
    Application title.
    """

    api_key: SecretStr
    """
    API-Key to secure endpoint access.
    """

    database_dsn: SecretStr
    """
    DSN for database connection.
    """

    test_database_dsn: SecretStr | None = None
    """
    DSN for test database connection.
    """

    redis_dsn: SecretStr
    """
    DSN for Redis connection.
    """

    s3_dsn: SecretStr
    """
    DSN for S3 connection.
    """

    s3_region: str = "eu-central-1"
    """
    AWS region to connect to.
    """

    s3_username: SecretStr
    """
    AWS access key.
    """

    s3_password: SecretStr
    """
    AWS secret key.
    """

    s3_remote_dsn: SecretStr | None = None
    """
    DSN for generating remote direct URLs.
    """

    rabbitmq_dsn: SecretStr
    """
    DSN for RabbitMQ connection.
    """

    result_backend_dsn: str = "rpc://"
    """
    DSN for retrieving task results.
    """

    min_player_amount: int = 3
    """
    Minimum player count in any game.
    """

    max_player_amount: int = 8
    """
    Maximum player count in any game.
    """

    guaranteed_unique_words_count: int = 30
    """
    Count of words required to view in any game to be able to be repeated.
    """

    telegram_bot_start_url: str = "https://t.me/SpotTheSpyBot?start={payload}"
    """
    Telegram bot URL template used to generate a bot deeplink.
    """

    default_redis_key: str = "spotthespy"
    """
    Default prefix for all Redis keys managed by Redis controllers.
    """


# Main Config instance.
config = Config(_env_file=".env")
