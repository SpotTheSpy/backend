from typing import ClassVar, Self

from app.assets.objects.s3 import AbstractS3Object


class QRCode(AbstractS3Object):
    """
    Represents a QR-Code image in an S3 Storage.
    """

    bucket: ClassVar[str] = "qrcodes"

    file_format: str = "jpg"

    @classmethod
    def new(
            cls,
            name: str,
            content: bytes
    ) -> Self:
        """
        Create a new QR-Code instance.

        :param name: Name of the QR-Code.
        :param content: JPEG image of a QR-Code in a bytes object.
        :return: QR-Code instance.
        """

        return cls(
            name=name,
            content=content
        )
