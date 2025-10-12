from starlette import status

from app.api.v1.exceptions.http import HTTPError


class AlreadyExistsError(HTTPError):
    """
    Raised when object with the same provided unique parameters already exists.
    """

    status_code = status.HTTP_409_CONFLICT
