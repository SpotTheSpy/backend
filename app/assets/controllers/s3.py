from contextlib import asynccontextmanager
from typing import AsyncGenerator, TypeVar, Any, Generic

from aiobotocore.client import AioBaseClient
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from pydantic.dataclasses import dataclass

from app.assets.controllers.abstract import AbstractController
from app.assets.objects.s3 import AbstractS3Object

T = TypeVar('T', bound=AbstractS3Object)


@dataclass(frozen=True)
class S3Config:
    dsn: str
    region: str
    username: str
    password: str


class S3Controller(Generic[T], AbstractController):
    def __init__(
            self,
            config: S3Config
    ) -> None:
        self._config = config

    @property
    def bucket(self) -> str:
        try:
            return self.object_class.bucket
        except NameError:
            raise ValueError("Bucket attribute in generic redis object class is not set")

    async def set(
            self,
            value: T
    ) -> None:
        await self._set(self.bucket, value.primary_key, value.content)

    async def get(
            self,
            primary_key: Any
    ) -> T | None:
        value: bytes = await self._get(self.bucket, primary_key)
        return None if value is None else T.new(name=primary_key, value=value)

    async def exists(
            self,
            primary_key: Any
    ) -> bool:
        return await self._exists(self.bucket, primary_key)

    async def remove(
            self,
            primary_key: Any
    ) -> None:
        await self._remove(self.bucket, primary_key)

    async def url(
            self,
            primary_key: Any,
            *,
            expire: int | None = None
    ) -> str | None:
        return await self._url(self.bucket, primary_key, expire=expire)

    async def _set(
            self,
            bucket: str,
            key: str,
            content: bytes
    ) -> None:
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
        async with self._get_client() as client:
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
        async with self._get_client() as client:
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
        async with self._get_client() as client:
            await client.delete_object(Bucket=bucket, Key=key)

    async def _url(
            self,
            bucket: str,
            key: str,
            *,
            expire: int | None = None
    ) -> str | None:
        if expire is None:
            expire = 3600

        async with self._get_client() as client:
            try:
                url: str = await client.generate_presigned_url(
                    "get_object",
                    Params={'Bucket': bucket, "Key": key},
                    ExpiresIn=expire
                )
            except ClientError:
                return

        return url

    @staticmethod
    def _name(
            name: str,
            file_format: str
    ) -> str:
        return f"{name}.{file_format}"

    @asynccontextmanager
    async def _get_client(self) -> AsyncGenerator[AioBaseClient, None]:
        session = get_session()
        async with session.create_client(
                "s3",
                endpoint_url=self._config.dsn,
                region_name=self._config.region,
                aws_access_key_id=self._config.username,
                aws_secret_access_key=self._config.password
        ) as client:
            yield client
