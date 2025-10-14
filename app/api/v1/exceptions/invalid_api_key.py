from starlette import status

from app.api.v1.exceptions.http import HTTPError


class InvalidAPIKeyError(HTTPError):
    """
    Raised when user provides an invalid API Key.
    """

    status_code = status.HTTP_401_UNAUTHORIZED
