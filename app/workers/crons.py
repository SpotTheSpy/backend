from asyncio import run, sleep
from typing import Tuple, List

from redis.asyncio import Redis

from app.assets.controllers.redis import RedisController
from app.assets.controllers.s3 import S3Config, S3Controller
from app.assets.objects.multi_device_active_player import MultiDeviceActivePlayer
from app.assets.objects.multi_device_game import MultiDeviceGame
from app.assets.objects.qr_code import QRCode
from app.workers.worker import worker, config


async def __async_cleanup() -> None:
    redis = Redis.from_url(config.redis_dsn.get_secret_value())
    s3_config = S3Config(
        config.s3_dsn.get_secret_value(),
        config.s3_region,
        config.s3_username.get_secret_value(),
        config.s3_password.get_secret_value(),
        config.s3_remote_dsn.get_secret_value() if config.s3_remote_dsn is not None else None
    )

    multi_device_games = RedisController[MultiDeviceGame](redis)
    multi_device_players = RedisController[MultiDeviceActivePlayer](redis)
    qr_codes = S3Controller[QRCode](s3_config)

    games: List[MultiDeviceGame] = []
    limit: int = 10
    offset: int = 0

    while True:
        new_games: Tuple[MultiDeviceGame, ...] = await multi_device_games.all(
            limit=limit,
            offset=offset,
            players_controller=multi_device_players,
            from_json_method=MultiDeviceGame.from_json_and_controllers
        )

        await sleep(0.25)

        if not new_games:
            break

        games.extend(new_games)
        offset += limit

    for game in games:
        if not game.players or await multi_device_players.get(game.host_id) is None:
            await game.unhost()
            await qr_codes.remove(QRCode.new(str(game.game_id), b"").primary_key)

            await sleep(1)

    await qr_codes.remove("blurred.jpg")


@worker.task(name="cleanup")
def cleanup() -> None:
    run(__async_cleanup())
