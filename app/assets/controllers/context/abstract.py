from abc import ABC, abstractmethod
from typing import Any


class Context(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def init(
            self,
            *args: Any,
            **kwargs: Any
    ) -> None:
        pass

    @abstractmethod
    def to_json(self) -> Any:
        pass
