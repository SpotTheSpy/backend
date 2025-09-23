from abc import ABC, abstractmethod

from pydantic.dataclasses import dataclass

from app.assets.objects.base import BaseObject


@dataclass
class RedisObject(BaseObject, ABC):
    @abstractmethod
    async def save(self) -> None: pass

    @abstractmethod
    async def clear(self) -> None: pass
