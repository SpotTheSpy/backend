from random import shuffle
from typing import Any, Dict, Optional, TYPE_CHECKING, List, Tuple
from uuid import UUID

from app.assets.controllers.context.abstract import Context
from app.assets.objects.multi_device_player import MultiDevicePlayer

if TYPE_CHECKING:
    from app.assets.objects.multi_device_game import MultiDeviceGame


class MultiDevicePlayers(Context):
    def __init__(self) -> None:
        self._players: Dict[UUID, MultiDevicePlayer] = {}
        self._game: Optional['MultiDeviceGame'] = None

    def init(
            self,
            players: List[Dict[str, Any]] | None,
            *,
            game: 'MultiDeviceGame'
    ) -> None:
        self._players.clear()
        self._game = game

        if players is None:
            return

        for player_json in players:
            player: MultiDevicePlayer | None = MultiDevicePlayer.from_json(
                player_json,
                game=game
            )

            if player is None:
                continue

            self.add(player)

    def to_json(self) -> List[Dict[str, Any]]:
        return [player.to_json() for player in self.list]

    @property
    def game(self) -> Optional['MultiDeviceGame'] | None:
        return self._game

    @property
    def ids(self) -> List[UUID]:
        return list(self._players.keys())

    @property
    def list(self) -> List[MultiDevicePlayer]:
        return list(self._players.values())

    @property
    def size(self) -> int:
        return len(self._players)

    def add(
            self,
            player: MultiDevicePlayer
    ) -> None:
        if not self.exists(player.user_id):
            self._players[player.user_id] = player

    def get(
            self,
            uuid: UUID
    ) -> MultiDeviceGame | None:
        return self._players.get(uuid)

    def exists(
            self,
            uuid: UUID
    ) -> bool:
        return uuid in self._players

    def remove(
            self,
            uuid: UUID
    ) -> None:
        if self.exists(uuid):
            self._players.pop(uuid)

    def shuffle(self) -> None:
        players_items: List[Tuple[UUID, MultiDevicePlayer]] = list(self._players.items())
        shuffle(players_items)
        self._players = dict(players_items)
