from starlette import status


class HTTPError(Exception):
    """
    Raised when a business-logic error is encountered.
    """

    status_code = status.HTTP_400_BAD_REQUEST
