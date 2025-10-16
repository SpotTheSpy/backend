from enum import StrEnum


class Payload(StrEnum):
    """
    Type of payload which can be inserted into bot deeplink start command.
    Used to determine required action.
    """

    JOIN = "join"
