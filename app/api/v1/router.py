from fastapi import APIRouter

from app.api.v1.single_device_games.router import single_device_games_router
from app.api.v1.users.router import users_router

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(users_router)
v1_router.include_router(single_device_games_router)
