from starlette import status

from app.api.v1.exceptions.http import HTTPError


class AlreadyInGameError(HTTPError):
    """
    Raised when a user who tries to host or join a game is already in another game.
    """

    status_code = status.HTTP_409_CONFLICT
