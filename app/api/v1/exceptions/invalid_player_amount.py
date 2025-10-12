from starlette import status

from app.api.v1.exceptions.http import HTTPError


class InvalidPlayerAmountError(HTTPError):
    """
    Raised when user tries to perform an action which will result in an invalid player count in the game.

    Possible when user tries to join a full game, or start a game with less than minimal acceptable player count.
    """

    status_code = status.HTTP_406_NOT_ACCEPTABLE
