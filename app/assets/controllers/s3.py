from contextlib import asynccontextmanager
from typing import AsyncGenerator, TypeVar, Any, Generic, Self

from aiobotocore.client import AioBaseClient
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from pydantic.dataclasses import dataclass

from app.assets.controllers.abstract import AbstractController
from app.assets.objects.s3 import AbstractS3Object
from config import Config

T = TypeVar('T', bound=AbstractS3Object)


@dataclass(frozen=True)
class S3Config:
    """
    S3 credentials model used to generate an S3 client session.

    Attributes:
        dsn: S3 storage DSN.
        region: AWS region.
        username: AWS access key.
        password: AWS secret key.
        remote_dsn: S3 remote DSN for generating direct URLs for remote usage.
    """

    dsn: str
    """
    S3 storage DSN.
    """

    region: str
    """
    AWS region.
    """

    username: str
    """
    AWS access key.
    """

    password: str
    """
    AWS secret key.
    """

    remote_dsn: str | None = None
    """
    S3 remote DSN for generating direct URLs for remote usage.
    """

    @classmethod
    def from_config(
            cls,
            config: Config
    ) -> Self:
        """
        Create S3 config instance Config object.

        :param config: Config object.
        :return: S3 config instance.
        """

        return cls(
            config.s3_dsn.get_secret_value(),
            config.s3_region,
            config.s3_username.get_secret_value(),
            config.s3_password.get_secret_value(),
            config.s3_remote_dsn.get_secret_value() if config.s3_remote_dsn is not None else None
        )


class S3Controller(AbstractController, Generic[T]):
    """
    S3 controller class.

    Provides control over file objects inside an S3 storage.

    Please make sure to select a generic model after a class name definition,
    otherwise any method execution may result in an error.

    Example usage:

    '''
    controller = S3Controller[S3Object](...)
    '''
    """

    def __init__(
            self,
            config: S3Config
    ) -> None:
        """
        Initialize S3 controller instance.

        :param config: S3 config instance for generating S3 client sessions.
        """

        self._config = config

    @property
    def bucket(self) -> str:
        """
        Object class bucket name, required in every S3 object class to define object bucket.

        :raise ValueError: If the bucket name is not defined.
        :return: Object class bucket name.
        """

        try:
            return self.object_class.bucket
        except NameError:
            raise ValueError("Bucket attribute in generic redis object class is not set")

    async def set(
            self,
            value: T
    ) -> None:
        """
        Upload new file by a primary key.

        :param value: Value to be uploaded.
        """

        await self._set(self.bucket, value.primary_key, value.content)

    async def get(
            self,
            primary_key: Any
    ) -> T | None:
        """
        Retrieve value by primary key.

        :param primary_key: Primary key for the value to be retrieved.
        :return: Value if exists, None otherwise.
        """

        value: bytes = await self._get(self.bucket, primary_key)
        return None if value is None else T.new(name=primary_key, value=value)

    async def exists(
            self,
            primary_key: Any
    ) -> bool:
        """
        Check if primary key exists.

        :param primary_key: Primary key to be checked.
        :return: True if exists, False otherwise.
        """

        return await self._exists(self.bucket, primary_key)

    async def remove(
            self,
            primary_key: Any
    ) -> None:
        """
        Remove value by primary key.

        :param primary_key: Primary key for the value to be removed.
        """

        await self._remove(self.bucket, primary_key)

    async def url(
            self,
            primary_key: Any,
            *,
            expire: int | None = None
    ) -> str | None:
        """
        Generate a direct URL to a value file by primary key.

        :param primary_key: Primary key for the URL to be generated.
        :param expire: Expiration time in seconds, defaults to 1 hour.
        :return: Direct URL if exists, None otherwise.
        """

        return await self._url(self.bucket, primary_key, expire=expire)

    async def _set(
            self,
            bucket: str,
            key: str,
            content: bytes
    ) -> None:
        """
        Upload data by bucket name and key.

        :param bucket: Bucket name.
        :param key: File key.
        :param content: Data in bytes.
        """

        async with self._get_client() as client:
            try:
                await client.head_bucket(Bucket=bucket)
            except ClientError:
                await client.create_bucket(Bucket=bucket)

            await client.put_object(Bucket=bucket, Key=key, Body=content)

    async def _get(
            self,
            bucket: str,
            key: str
    ) -> bytes | None:
        """
        Retrieve data by bucket name and key.

        :param bucket: Bucket name.
        :param key: File key.
        :return: Data in bytes if exists, None otherwise.
        """

        async with self._get_client() as client:
            try:
                await client.head_bucket(Bucket=bucket)
            except ClientError:
                await client.create_bucket(Bucket=bucket)

            try:
                result: dict = await client.get_object(Bucket=bucket, Key=key)
            except ClientError:
                return

        return await result.get("Body").read()

    async def _exists(
            self,
            bucket: str,
            key: str
    ) -> bool:
        """
        Check if data exists by bucket name and key.

        :param bucket: Bucket name.
        :param key: File key.
        :return: True if exists, False otherwise.
        """

        async with self._get_client() as client:
            try:
                await client.head_bucket(Bucket=bucket)
            except ClientError:
                await client.create_bucket(Bucket=bucket)

            try:
                await client.head_object(Bucket=bucket, Key=key)
                return True
            except ClientError:
                return False

    async def _remove(
            self,
            bucket: str,
            key: str
    ) -> None:
        """
        Remove data by bucket name and key.

        :param bucket: Bucket name.
        :param key: File key.
        """

        async with self._get_client() as client:
            try:
                await client.head_bucket(Bucket=bucket)
            except ClientError:
                await client.create_bucket(Bucket=bucket)

            await client.delete_object(Bucket=bucket, Key=key)

    async def _url(
            self,
            bucket: str,
            key: str,
            *,
            expire: int | None = None
    ) -> str | None:
        """
        Generate a direct URL to data by bucket name and key.

        :bucket: Bucket name.
        :param key: File key.
        :param expire: Expiration time in seconds, defaults to 1 hour.
        :return: Direct URL if exists, None otherwise.
        """

        if expire is None:
            expire = 3600

        async with self._get_client(endpoint_url=self._config.remote_dsn) as client:
            try:
                url: str = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=expire
                )
            except ClientError:
                return

        return url

    @asynccontextmanager
    async def _get_client(
            self,
            *,
            endpoint_url: str | None = None
    ) -> AsyncGenerator[AioBaseClient, None]:
        """
        Generate an S3 client session.
        :param endpoint_url: Optional endpoint URL for S3 client.
        :return: S3 client session.
        """

        session = get_session()
        async with session.create_client(
                "s3",
                endpoint_url=endpoint_url or self._config.dsn,
                region_name=self._config.region,
                aws_access_key_id=self._config.username,
                aws_secret_access_key=self._config.password
        ) as client:
            yield client
