from starlette import status

from app.api.v1.exceptions.http import HTTPError


class InvalidPlayerAmountError(HTTPError):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
