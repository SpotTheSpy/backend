from typing import Any, Dict, TYPE_CHECKING, List, Generic, TypeVar

from pydantic import BaseModel, Field

from app.assets.objects.abstract import AbstractObject

if TYPE_CHECKING:
    from app.assets.objects.multi_device_game import MultiDeviceGame
else:
    MultiDeviceGame = Any

T = TypeVar('T', bound=AbstractObject)


class Context(Generic[T], BaseModel):
    _values: Dict[Any, T] = Field(default_factory=dict)

    @classmethod
    def model_validate(
        cls,
        obj: List[Any],
        **kwargs: Any
    ) -> 'Context[T]':
        context = cls()

        for value in obj:
            validated: T | None = T.from_json(value, **kwargs)
            if validated is not None:
                context.add(validated)

        return context

    def model_dump(
        self,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        return [value.model_dump(**kwargs) for value in self.list]

    @property
    def ids(self) -> List[Any]:
        return list(self._values.keys())

    @property
    def list(self) -> List[T]:
        return list(self._values.values())

    @property
    def size(self) -> int:
        return len(self._values)

    def add(
            self,
            value: T
    ) -> None:
        if not self.exists(value.primary_key):
            self._values[value.primary_key] = value

    def get(
            self,
            primary_key: Any
    ) -> T | None:
        return self._values.get(primary_key)

    def exists(
            self,
            primary_key: Any
    ) -> bool:
        return primary_key in self._values

    def remove(
            self,
            primary_key: Any
    ) -> None:
        if self.exists(primary_key):
            self._values.pop(primary_key)
