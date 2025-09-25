from typing import Any, Dict
from uuid import UUID

from pydantic.dataclasses import dataclass

from app.assets.objects.base import BaseObject


@dataclass
class MultiDevicePlayer(BaseObject):
    game_id: UUID
    user_id: UUID

    @classmethod
    def from_json(
            cls,
            data: Dict[str, Any]
    ) -> Any:
        return cls(**data)

    def to_json(self) -> Dict[str, Any]:
        return {
            "game_id": str(self.game_id),
            "user_id": str(self.user_id)
        }
