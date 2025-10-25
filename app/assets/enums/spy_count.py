from enum import StrEnum
from random import shuffle, random
from typing import Tuple, List, Self


class SpyCount(StrEnum):
    """
    Count of spies in game.
    """

    SINGLE = "single"
    DOUBLE = "double"
    RANDOM = "random"

    def get_indices(
            self,
            player_amount: int
    ) -> Tuple[int, ...]:
        """
        Retrieve random indices of spies in game from player count.

        If spy count is random, there is a 45% chance of either having one or two spies,
        and a 10% chance of having no spies.

        :param player_amount: Count of players.
        :return: Tuple of player indices.
        """

        indices: List[int] = list(range(player_amount))
        shuffle(indices)

        selected_indices = []
        selected: bool = False

        value: Self = self

        if value == self.RANDOM:
            chance: float = random()

            if chance < 0.1:
                selected = True
            else:
                value = self.SINGLE if chance < 0.55 else self.DOUBLE

        if not selected:
            selected_indices: List[int] = indices[:1] if value == self.SINGLE else indices[:2]

        return tuple(sorted(selected_indices))
