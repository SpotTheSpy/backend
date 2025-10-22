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

        value: Self = self

        if value == self.RANDOM:
            chance: float = random()

            if chance < 0.1:
                return tuple()

            value = self.SINGLE if chance < 0.55 else self.DOUBLE

        return tuple(indices[:1]) if value == self.SINGLE else tuple(indices[:2])
