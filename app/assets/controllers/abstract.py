from abc import ABC, abstractmethod
from typing import Type, TypeVar, Any, Generic

from app.assets.objects.abstract import AbstractObject

T = TypeVar('T', bound=AbstractObject)


class AbstractController(ABC, Generic[T]):
    """
    Abstract controller class.

    Requires implementation of basic methods which can be performed with a generic model.

    Please make sure to select a generic model after a class name definition,
    otherwise any method execution may result in an error.

    Example usage:

    '''
    controller = AbstractController[Object](...)
    '''
    """

    @abstractmethod
    async def set(
            self,
            value: T
    ) -> None:
        """
        Set new value by a primary key.

        :param value: Value to be set.
        """

    @abstractmethod
    async def get(
            self,
            primary_key: Any
    ) -> T | None:
        """
        Retrieve value by primary key.

        :param primary_key: Primary key for the value to be retrieved.
        :return: Value if exists, None otherwise.
        """

    @abstractmethod
    async def exists(
            self,
            primary_key: Any
    ) -> bool:
        """
        Check if primary key exists.

        :param primary_key: Primary key to be checked.
        :return: True if exists, False otherwise.
        """

    @abstractmethod
    async def remove(
            self,
            primary_key: Any
    ) -> None:
        """
        Remove value by primary key.

        :param primary_key: Primary key for the value to be removed.
        """

    @property
    def object_class(self) -> Type[T]:
        """
        Class of an object, selected as a generic.

        :raise ValueError: If generic object class is not selected.
        :return: Object class.
        """

        if not hasattr(self, "__orig_class__"):
            raise ValueError("Generic object class is not set")
        classes = getattr(self, "__orig_class__").__args__
        if not classes:
            raise ValueError("Generic object class is not set")

        return classes[0]
