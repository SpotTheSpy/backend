from abc import ABC, abstractmethod
from typing import Any, Dict

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class AbstractObject(ABC):
    @property
    @abstractmethod
    def primary_key(self) -> Any:
        pass

    @classmethod
    @abstractmethod
    def new(cls, *args, **kwargs) -> Any:
        pass

    @classmethod
    @abstractmethod
    def from_json(cls, *args, **kwargs) -> Any:
        pass

    @abstractmethod
    def to_json(self) -> Dict[str, Any]:
        pass
