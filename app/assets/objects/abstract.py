from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Self

from pydantic import BaseModel, ValidationError


class AbstractObject(BaseModel, ABC, arbitrary_types_allowed=True):
    @property
    @abstractmethod
    def primary_key(self) -> Any:
        pass

    @classmethod
    @abstractmethod
    def new(cls, *args, **kwargs) -> Any:
        pass

    @classmethod
    def from_json(
            cls,
            data: Dict[str, Any],
            **kwargs: Any
    ) -> Optional[Self]:
        data.update(kwargs)

        try:
            return cls.model_validate(data)
        except ValidationError:
            pass

    def to_json(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")
