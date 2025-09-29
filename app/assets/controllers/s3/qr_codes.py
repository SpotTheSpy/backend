import asyncio
from io import BytesIO
from typing import Tuple
from uuid import UUID

from PIL import Image, ImageOps
from PIL.ImageDraw import Draw
from segno import QRCode, make

from app.assets.controllers.s3.abstract import S3Controller


class QRCodeGenerator:
    def __init__(
            self,
            fill_color: str,
            back_color: str,
            pixel_size: int = 28,
            radius: int = 12,
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


class QRCodesController(S3Controller):
    generator = QRCodeGenerator(
        "#050B10",
        "#F0F0F0"
    )

    def bucket(self) -> str:
        return "qrcodes"

    async def upload_qr_code(
            self,
            game_id: UUID,
            url: str
    ) -> None:
        await self.add(
            str(game_id),
            await self.generator.generate(url)
        )

    async def get_qr_code_url(
            self,
            game_id: UUID
    ) -> str | None:
        return await self.url(str(game_id))

    async def delete_qr_code(
            self,
            game_id: UUID
    ) -> None:
        await self.delete(str(game_id))
