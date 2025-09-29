from abc import abstractmethod, ABC
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from aiobotocore.client import AioBaseClient
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class S3Config:
    dsn: str
    region: str
    username: str
    password: str


@dataclass
class S3Controller(ABC):
    s3: S3Config

    @abstractmethod
    def bucket(self) -> str: pass

    async def add(
            self,
            name: str,
            content: bytes
    ) -> None:
        await self._create_bucket_if_not_exists()

        async with self._get_client() as client:
            await client.put_object(Bucket=self.bucket(), Key=name, Body=content)

    async def get(
            self,
            name: str
    ) -> bytes | None:
        async with self._get_client() as client:
            try:
                result: dict = await client.get_object(Bucket=self.bucket(), Key=name)
            except ClientError:
                return

        return await result.get("Body").read()

    async def url(
            self,
            name: str,
            *,
            expire: int = 60
    ) -> str | None:
        async with self._get_client() as client:
            try:
                url: str = await client.generate_presigned_url(
                    "get_object",
                    Params={'Bucket': self.bucket(), "Key": name},
                    ExpiresIn=expire
                )
            except ClientError:
                return

        return url

    async def delete(
            self,
            name: str
    ) -> None:
        async with self._get_client() as client:
            await client.delete_object(Bucket=self.bucket(), Key=name)

    async def _create_bucket_if_not_exists(self) -> None:
        async with self._get_client() as client:
            try:
                await client.head_bucket(Bucket=self.bucket())
            except ClientError:
                await client.create_bucket(Bucket=self.bucket())

    @asynccontextmanager
    async def _get_client(self) -> AsyncGenerator[AioBaseClient, None]:
        session = get_session()
        async with session.create_client(
                "s3",
                endpoint_url=self.s3.dsn,
                region_name=self.s3.region,
                aws_access_key_id=self.s3.username,
                aws_secret_access_key=self.s3.password,
        ) as client:
            yield client
