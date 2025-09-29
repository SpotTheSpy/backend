from starlette import status

from app.api.v1.exceptions.http import HTTPError


class NotInGameError(HTTPError):
    status_code = status.HTTP_409_CONFLICT
