from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Self

from pydantic import BaseModel, ValidationError


class AbstractObject(BaseModel, ABC, arbitrary_types_allowed=True):
    """
    Abstract game object class.

    Used to define any structure which is a part of the game,
    such as a game itself, player, or any other entity.
    """

    @property
    @abstractmethod
    def primary_key(self) -> Any:
        """
        Main and unique key of any object, a value by which any object can be explicitly identified.
        :return: Primary key of any type, must be JSON-Serializable.
        """

    @classmethod
    @abstractmethod
    def new(cls, *args, **kwargs) -> Any:
        """
        Generate a new object instance using only required parameters.

        :return: An object instance.
        """

    @classmethod
    def from_json(
            cls,
            data: Dict[str, Any],
            **kwargs: Any
    ) -> Optional[Self]:
        """
        Reconstruct an object instance from a JSON-Serialized dictionary.

        :param data: Dictionary to reconstruct an object instance.
        :param kwargs: Any additional JSON-Serializable parameters.
        :return: An object instance if validated successfully, else None.
        """

        data.update(kwargs)

        try:
            return cls.model_validate(data)
        except ValidationError:
            pass

    def to_json(self) -> Dict[str, Any]:
        """
        Serialize an object instance to a JSON-Serializable dictionary.

        :raise PydanticSerializationError: If serialization fails.
        :return: A JSON-Serializable dictionary.
        """

        return self.model_dump(mode="json")
