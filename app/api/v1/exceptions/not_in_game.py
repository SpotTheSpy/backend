from starlette import status

from app.api.v1.exceptions.http import HTTPError


class NotInGameError(HTTPError):
    """
    Raised when user tries to perform an action in a specific game while not being in it.
    """

    status_code = status.HTTP_409_CONFLICT
