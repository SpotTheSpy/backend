from starlette import status

from app.api.v1.exceptions.http import HTTPError


class NotFoundError(HTTPError):
    """
    Raised when an object is not found.
    """

    status_code = status.HTTP_404_NOT_FOUND
