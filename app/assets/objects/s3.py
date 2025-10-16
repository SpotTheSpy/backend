from abc import ABC
from typing import ClassVar

from app.assets.objects.abstract import AbstractObject


class AbstractS3Object(AbstractObject, ABC):
    """
    Abstract class for S3 objects.

    This is an abstract class for objects which represent specific files in an S3 storage.

    Every S3 object class must have a bucket class argument, which determines to which bucket it will be saved.
    If the bucket does not exist, it will be created right before saving.

    Primary key, by which an object is saved, is constructed from name and a file format, connected using dot sign.

    Value is a bytes object represented by content parameter.
    """

    bucket: ClassVar[str]
    """
    Object class bucket name.
    """

    name: str
    """
    File name without an extension.
    """

    file_format: str
    """
    File extension name without a dot sign
    """

    content: bytes
    """
    Content of the file.
    """

    @property
    def primary_key(self) -> str:
        """
        File name with a proper extension.
        :return: File name as a string.
        """

        return f"{self.name}.{self.file_format}"
