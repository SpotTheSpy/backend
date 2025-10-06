import asyncio
from uuid import UUID

from celery.result import AsyncResult

from app.assets.controllers.s3.abstract import S3Controller
from app.workers.tasks import generate_qr_code, upload_to_s3, delete_from_s3


class QRCodesController(S3Controller):
    _FILL_COLOR: str = "#050B10"
    _BACK_COLOR: str = "#F0F0F0"

    def bucket(self) -> str:
        return "qrcodes"

    async def upload_qr_code(
            self,
            game_id: UUID,
            url: str
    ) -> None:
        task: AsyncResult = await asyncio.to_thread(
            generate_qr_code.delay,
            url,
            self._FILL_COLOR,
            self._BACK_COLOR
        )

        qr_code: bytes = await asyncio.to_thread(
            task.get,
            timeout=10,
            **{}
        )

        task: AsyncResult = await asyncio.to_thread(
            upload_to_s3.delay,
            self.bucket(),
            f"{game_id}.jpg",
            qr_code
        )

        await asyncio.to_thread(
            task.get,
            timeout=10,
            **{}
        )

    async def get_qr_code_url(
            self,
            game_id: UUID
    ) -> str | None:
        return await self.url(f"{game_id}.jpg")

    async def get_blurred_url(self) -> str | None:
        return await self.url("blurred.jpg")

    async def delete_qr_code(
            self,
            game_id: UUID
    ) -> None:
        await asyncio.to_thread(
            delete_from_s3,
            self.bucket(),
            f"{game_id}.jpg"
        )
