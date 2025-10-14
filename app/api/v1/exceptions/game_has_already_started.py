from starlette import status

from app.api.v1.exceptions.http import HTTPError


class GameHasAlreadyStartedError(HTTPError):
    """
    Raised when user tries to perform an action which cannot be processed in a started game.
    """

    status_code = status.HTTP_400_BAD_REQUEST
