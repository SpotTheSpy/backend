import asyncio
import sys
from asyncio import SelectorEventLoop

import uvicorn.loops.asyncio

from app.logging import API_LOG_CONFIG

if __name__ == "__main__":
    if sys.platform == "win32":  # Using SelectorEventLoop on Windows to avoid psycopg exceptions
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        uvicorn.loops.asyncio.asyncio_loop_factory = lambda use_subprocess: SelectorEventLoop

    uvicorn.run(
        "app.asgi:app",
        host="0.0.0.0",
        port=8000,
        loop="asyncio",
        log_config=API_LOG_CONFIG
    )
