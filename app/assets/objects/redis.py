from abc import ABC, abstractmethod

from pydantic.dataclasses import dataclass

from app.assets.objects.abstract import AbstractObject


@dataclass
class AbstractRedisObject(AbstractObject, ABC):
    @abstractmethod
    async def save(self) -> None:
        pass

    @abstractmethod
    async def clear(self) -> None:
        pass
