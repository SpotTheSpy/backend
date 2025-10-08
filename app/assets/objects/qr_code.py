from typing import ClassVar, Self

from app.assets.objects.s3 import AbstractS3Object


class QRCode(AbstractS3Object):
    bucket: ClassVar[str] = "qrcodes"

    file_format: str = "jpg"

    @classmethod
    def new(
            cls,
            name: str,
            content: bytes
    ) -> Self:
        return cls(
            name=name,
            content=content
        )
