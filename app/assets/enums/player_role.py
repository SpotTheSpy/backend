from enum import StrEnum


class PlayerRole(StrEnum):
    """
    Role of a player in the game.
    """

    CITIZEN = "citizen"
    SPY = "spy"
