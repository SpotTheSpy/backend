from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

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
    ) -> Optional['AbstractObject']:
        try:
            return cls.model_validate(data, **kwargs)
        except ValidationError:
            pass

    def to_json(
            self,
            **kwargs: Any
    ) -> Dict[str, Any]:
        return self.model_dump(mode="json", **kwargs)
