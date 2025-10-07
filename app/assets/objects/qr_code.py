from typing import Any, ClassVar, Self

from app.assets.objects.s3 import AbstractS3Object


class QRCode(AbstractS3Object):
    bucket: ClassVar[str] = "qrcodes"

    @classmethod
    def new(
            cls,
            name: str,
            file_format: str,
            content: bytes
    ) -> Self:
        return cls(
            name=name,
            file_format=file_format,
            content=content
        )
