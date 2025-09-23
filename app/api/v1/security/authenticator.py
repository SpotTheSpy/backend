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
    api_key_header = APIKeyHeader(name="API-Key")

    def __init__(
            self,
            *,
            api_key: str
    ) -> None:
        self._api_key = api_key
        self._ph = PasswordHasher()

    async def hash(
            self,
            string: str
    ) -> str:
        return await asyncio.to_thread(self._ph.hash, string)

    async def verify(
            self,
            string: str,
            hashed_string: str
    ) -> bool:
        try:
            await asyncio.to_thread(self._ph.verify, hashed_string, string)
            return True
        except VerifyMismatchError:
            return False

    @staticmethod
    def dependency(config: Annotated[Config, Depends(config_dependency)]) -> 'Authenticator':
        return Authenticator(api_key=config.api_key.get_secret_value())

    @staticmethod
    def verify_api_key() -> Depends:
        def __verify_api_key(
                api_key: Annotated[str, Security(Authenticator.api_key_header)],
                config: Annotated[Config, Depends(config_dependency)]
        ) -> None:
            if api_key != config.api_key.get_secret_value():
                raise InvalidAPIKeyError("Provided API key is invalid")

        return Depends(__verify_api_key)
