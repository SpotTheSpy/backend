from abc import ABC, abstractmethod
from typing import Type, TypeVar, Any, Generic

from app.assets.objects.abstract import AbstractObject

T = TypeVar('T', bound=AbstractObject)


class AbstractController(ABC, Generic[T]):
    @abstractmethod
    async def set(
            self,
            value: T
    ) -> None:
        pass

    @abstractmethod
    async def get(
            self,
            primary_key: Any
    ) -> T | None:
        pass

    @abstractmethod
    async def exists(
            self,
            primary_key: Any
    ) -> bool:
        pass

    @abstractmethod
    async def remove(
            self,
            primary_key: Any
    ) -> None:
        pass

    @property
    def object_class(self) -> Type[T]:
        if not hasattr(self, "__orig_class__"):
            raise ValueError("Generic redis object class is not set")
        classes = getattr(self, "__orig_class__").__args__
        if not classes:
            raise ValueError("Generic redis object class is not set")

        return classes[0]
