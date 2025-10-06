import asyncio
import json
from contextlib import asynccontextmanager
from io import BytesIO
from typing import Any, AsyncGenerator, Tuple

from PIL import Image, ImageOps
from PIL.ImageDraw import Draw
from aiobotocore.client import AioBaseClient
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError
from segno import QRCode, make

from app.workers.worker import worker, config


@asynccontextmanager
async def __get_client() -> AsyncGenerator[AioBaseClient, None]:
    session = get_session()
    async with session.create_client(
            "s3",
            endpoint_url=config.s3_dsn.get_secret_value(),
            region_name=config.s3_region,
            aws_access_key_id=config.s3_username.get_secret_value(),
            aws_secret_access_key=config.s3_password.get_secret_value()
    ) as client:
        yield client


class QRCodeGenerator:
    def __init__(
            self,
            fill_color: str,
            back_color: str,
            pixel_size: int = 14,
            radius: int = 6,
            border: int = 16,
            error: str = "Q"
    ) -> None:
        self.fill_color = fill_color
        self.back_color = back_color
        self.pixel_size = pixel_size
        self.radius = radius
        self.border = border
        self.error = error

    async def generate(
            self,
            url: str
    ) -> bytes:
        return await asyncio.to_thread(self._generate, url)

    def _generate(
            self,
            url: str
    ) -> bytes:
        buffer = BytesIO()

        qr: QRCode = make(url, self.error)
        matrix: Tuple[bytearray, ...] = qr.matrix

        image_size: int = len(matrix) * self.pixel_size
        image = Image.new("RGB", (image_size, image_size), self.back_color)
        draw = Draw(image)

        for y, row in enumerate(matrix):
            for x, pixel in enumerate(row):
                if pixel:
                    self._draw_filled_pixel(draw, matrix, x, y)

        ImageOps.expand(
            image,
            border=self.border + self.pixel_size,
            fill=self.back_color
        ).save(buffer, format="JPEG")

        buffer.seek(0)
        return buffer.read()

    def _draw_filled_pixel(
            self,
            draw: Draw,
            matrix: Tuple[bytearray, ...],
            x: int,
            y: int
    ) -> None:
        x0, y0 = x * self.pixel_size, y * self.pixel_size
        x1, y1 = (x + 0.5) * self.pixel_size - 1, (y + 0.5) * self.pixel_size - 1
        x2, y2 = (x + 0.5) * self.pixel_size, (y + 0.5) * self.pixel_size
        x3, y3 = (x + 1) * self.pixel_size - 1, (y + 1) * self.pixel_size - 1

        draw.rounded_rectangle((x0, y0, x3, y3), radius=self.radius, fill=self.fill_color)

        if self._is_filled(matrix, x + 1, y):
            draw.rectangle((x2, y0, x3, y3), fill=self.fill_color)
        if self._is_filled(matrix, x - 1, y):
            draw.rectangle((x0, y0, x1, y3), fill=self.fill_color)
        if self._is_filled(matrix, x, y + 1):
            draw.rectangle((x0, y2, x3, y3), fill=self.fill_color)
        if self._is_filled(matrix, x, y - 1):
            draw.rectangle((x0, y0, x3, y1), fill=self.fill_color)

    @staticmethod
    def _is_filled(
            matrix: Tuple[bytearray, ...],
            x: int,
            y: int
    ) -> bool:
        if x < 0 or y < 0 or x >= len(matrix) or y >= len(matrix):
            return False

        return matrix[y][x]


async def __async_save_to_redis(
        key: str,
        value: Any
) -> None:
    redis = Redis.from_url(config.redis_dsn.get_secret_value())
    await redis.set(key, value)


async def __async_clear_from_redis(key: str) -> None:
    redis = Redis.from_url(config.redis_dsn.get_secret_value())
    await redis.delete(key)


async def __async_upload_to_s3(
        bucket: str,
        name: str,
        content: bytes
) -> None:
    async with __get_client() as client:
        try:
            await client.head_bucket(Bucket=bucket)
        except ClientError:
            await client.create_bucket(Bucket=bucket)

        await client.put_object(Bucket=bucket, Key=name, Body=content)


async def __async_delete_from_s3(
        bucket: str,
        name: str
) -> None:
    async with __get_client() as client:
        await client.delete_object(Bucket=bucket, Key=name)


async def __async_generate_qr_code(
        url: str,
        fill_color: str,
        back_color: str
) -> bytes:
    generator = QRCodeGenerator(fill_color, back_color)
    return await generator.generate(url)


@worker.task(autoretry_for=(ConnectionError, TimeoutError), retry_backoff=True, max_retries=3)
def save_to_redis(
        key: str,
        value: Any
) -> None:
    asyncio.run(__async_save_to_redis(key, value))


@worker.task(autoretry_for=(ConnectionError, TimeoutError), retry_backoff=True, max_retries=3)
def clear_from_redis(key: str) -> None:
    asyncio.run(__async_clear_from_redis(key))


@worker.task(autoretry_for=(ClientError,), retry_backoff=True, max_retries=3)
def upload_to_s3(
        bucket: str,
        name: str,
        content: bytes
) -> None:
    asyncio.run(__async_upload_to_s3(bucket, name, content))


@worker.task(autoretry_for=(ClientError,), retry_backoff=True, max_retries=3)
def delete_from_s3(
        bucket: str,
        name: str
) -> None:
    asyncio.run(__async_delete_from_s3(bucket, name))


@worker.task()
def generate_qr_code(
        url: str,
        fill_color: str,
        back_color: str
) -> bytes:
    return asyncio.run(__async_generate_qr_code(url, fill_color, back_color))
