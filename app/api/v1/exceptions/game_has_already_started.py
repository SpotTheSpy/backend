from starlette import status

from app.api.v1.exceptions.http import HTTPError


class GameHasAlreadyStartedError(HTTPError):
    status_code = status.HTTP_400_BAD_REQUEST
