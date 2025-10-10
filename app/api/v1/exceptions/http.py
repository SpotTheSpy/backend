from starlette import status


class HTTPError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
