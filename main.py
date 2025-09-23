import asyncio
import sys

import uvicorn

from app.logging import API_LOG_CONFIG

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    uvicorn.run(
        "app.asgi:app",
        host="0.0.0.0",
        port=8000,
        loop="asyncio",
        log_config=API_LOG_CONFIG
    )
