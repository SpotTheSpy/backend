from enum import StrEnum


class PayloadType(StrEnum):
    """
    Type of payload which can be inserted into bot deeplink start command.
    Used to determine required action.
    """

    JOIN = "join"
