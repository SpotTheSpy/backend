import asyncio
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, Security
from fastapi.security import APIKeyHeader

from app.api.v1.exceptions.invalid_api_key import InvalidAPIKeyError
from app.dependencies import config_dependency
from config import Config


class Authenticator:
    """
    API Authentication tool.

    Verifies API Key by using a corresponding dependency method.
    """

    API_KEY_HEADER = APIKeyHeader(name="API-Key")

    def __init__(
            self,
            *,
            api_key: str,
            hasher: PasswordHasher | None = None,
    ) -> None:
        """
        Authenticator constructor.

        :param api_key: API Key to verify.
        :param hasher: Password hasher instance. If None, a default instance is used.
        """

        self._api_key = api_key
        self._hasher = hasher or PasswordHasher()

    async def hash(
            self,
            string: str
    ) -> str:
        return await asyncio.to_thread(self._hasher.hash, string)

    async def verify(
            self,
            string: str,
            hashed_string: str
    ) -> bool:
        try:
            await asyncio.to_thread(self._hasher.verify, hashed_string, string)
            return True
        except VerifyMismatchError:
            return False

    @staticmethod
    def dependency(config: Annotated[Config, Depends(config_dependency)]) -> 'Authenticator':
        """
        Authenticator dependency.

        Creates authenticator instance.

        :param config: Config dependency (Provided by FastAPI).
        :return: Authenticator instance.
        """

        return Authenticator(api_key=config.api_key.get_secret_value())

    @staticmethod
    def verify_api_key() -> Depends:
        """
        Dependency method for verifying API Key.

        Should be passed just as a function call.
        :return: Dependency instance.
        """

        def __verify_api_key(
                api_key: Annotated[str, Security(Authenticator.API_KEY_HEADER)],
                config: Annotated[Config, Depends(config_dependency)]
        ) -> None:
            if api_key != config.api_key.get_secret_value():
                raise InvalidAPIKeyError("Provided API key is invalid")

        return Depends(__verify_api_key)
