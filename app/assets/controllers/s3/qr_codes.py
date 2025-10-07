import asyncio
from uuid import UUID

from celery.result import AsyncResult

from app.assets.controllers.s3.abstract import S3Controller
from app.workers.tasks import generate_qr_code


class QRCodesController(S3Controller):
    def bucket(self) -> str:
        return "qrcodes"

    async def upload_qr_code(
            self,
            game_id: UUID,
            url: str
    ) -> None:
        task: AsyncResult = await asyncio.to_thread(generate_qr_code.delay, url)
        qr_code: bytes = await asyncio.to_thread(task.get, timeout=10, **{})

        await self.add(
            f"{game_id}.jpg",
            qr_code
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
        await self.delete(f"{game_id}.jpg")
