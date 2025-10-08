from abc import ABC
from typing import ClassVar, Any

from app.assets.objects.abstract import AbstractObject


class AbstractS3Object(AbstractObject, ABC):
    bucket: ClassVar[str]

    name: str
    file_format: str
    content: bytes

    @property
    def primary_key(self) -> Any:
        return f"{self.name}.{self.file_format}"
