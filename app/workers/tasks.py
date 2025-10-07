from io import BytesIO
from typing import Tuple

from PIL import Image, ImageOps
from PIL.ImageDraw import Draw
from segno import QRCode, make

from app.workers.worker import worker


class QRCodeGenerator:
    def __init__(
            self,
            *,
            fill_color: str | None = None,
            back_color: str | None = None,
            pixel_size: int | None = None,
            radius: int | None = None,
            border: int | None = None,
            error: str | None = None
    ) -> None:
        self.fill_color = fill_color or "#050B10"
        self.back_color = back_color or "#F0F0F0"
        self.pixel_size = pixel_size or 14
        self.radius = radius or 6
        self.border = border or 16
        self.error = error or "Q"

    def generate(
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


@worker.task()
def generate_qr_code(
        url: str,
        *,
        fill_color: str | None = None,
        back_color: str | None = None,
        pixel_size: int | None = None,
        radius: int | None = None,
        border: int | None = None,
        error: str | None = None
) -> bytes:
    generator = QRCodeGenerator(
        fill_color=fill_color,
        back_color=back_color,
        pixel_size=pixel_size,
        radius=radius,
        border=border,
        error=error
    )

    return generator.generate(url)
