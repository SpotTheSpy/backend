from starlette import status

from app.api.v1.exceptions.http import HTTPError


class AlreadyInGameError(HTTPError):
    status_code = status.HTTP_409_CONFLICT
