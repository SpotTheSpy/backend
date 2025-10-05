import asyncio
from typing import Dict, Any

from redis import Redis

from redis.exceptions import ConnectionError, TimeoutError
from app.asgi import config
from app.assets.controllers.redis.multi_device_games import MultiDeviceGamesController
from app.assets.controllers.redis.multi_device_players import MultiDevicePlayersController
from app.assets.controllers.redis.single_device_games import SingleDeviceGamesController
from app.assets.controllers.redis.single_device_players import SingleDevicePlayersController
from app.assets.objects.multi_device_active_player import MultiDeviceActivePlayer
from app.assets.objects.multi_device_game import MultiDeviceGame
from app.assets.objects.single_device_active_player import SingleDeviceActivePlayer
from app.assets.objects.single_device_game import SingleDeviceGame
from app.workers.worker import worker


async def __async_save_single_device_game(game_json: Dict[str, Any]):
    single_device_games = SingleDeviceGamesController(
        Redis.from_url(config.redis_dsn.get_secret_value())
    )

    game = SingleDeviceGame.from_json(game_json, controller=single_device_games)
    await single_device_games.set(single_device_games.key(game.game_id), game.to_json())


async def __async_save_single_device_player(player_json: Dict[str, Any]):
    single_device_players = SingleDevicePlayersController(
        Redis.from_url(config.redis_dsn.get_secret_value())
    )

    player = SingleDeviceActivePlayer.from_json(player_json, controller=single_device_players)
    await single_device_players.set(single_device_players.key(player.game_id), player.to_json())


async def __async_save_multi_device_game(game_json: Dict[str, Any]):
    multi_device_games = MultiDeviceGamesController(
        Redis.from_url(config.redis_dsn.get_secret_value())
    )

    game = MultiDeviceGame.from_json(game_json, controller=multi_device_games)
    await multi_device_games.set(multi_device_games.key(game.game_id), game.to_json())


async def __async_save_multi_device_player(player_json: Dict[str, Any]):
    multi_device_players = MultiDevicePlayersController(
        Redis.from_url(config.redis_dsn.get_secret_value())
    )

    player = MultiDeviceActivePlayer.from_json(player_json, controller=multi_device_players)
    await multi_device_players.set(multi_device_players.key(player.game_id), player.to_json())


async def __async_clear_single_device_game(game_json: Dict[str, Any]):
    single_device_games = SingleDeviceGamesController(
        Redis.from_url(config.redis_dsn.get_secret_value())
    )

    game = SingleDeviceGame.from_json(game_json, controller=single_device_games)
    await single_device_games.remove(single_device_games.key(game.game_id))


async def __async_clear_single_device_player(player_json: Dict[str, Any]):
    single_device_players = SingleDevicePlayersController(
        Redis.from_url(config.redis_dsn.get_secret_value())
    )

    player = SingleDeviceActivePlayer.from_json(player_json, controller=single_device_players)
    await single_device_players.remove(single_device_players.key(player.game_id))


async def __async_clear_multi_device_game(game_json: Dict[str, Any]):
    multi_device_games = MultiDeviceGamesController(
        Redis.from_url(config.redis_dsn.get_secret_value())
    )

    game = MultiDeviceGame.from_json(game_json, controller=multi_device_games)
    await multi_device_games.remove(multi_device_games.key(game.game_id))


async def __async_clear_multi_device_player(player_json: Dict[str, Any]):
    multi_device_players = MultiDevicePlayersController(
        Redis.from_url(config.redis_dsn.get_secret_value())
    )

    player = MultiDeviceActivePlayer.from_json(player_json, controller=multi_device_players)
    await multi_device_players.remove(multi_device_players.key(player.game_id))


@worker.task(autoretry_for=(ConnectionError, TimeoutError), retry_backoff=True, max_retries=3)
def save_single_device_game(data: Dict[str, Any]) -> None:
    asyncio.run(__async_save_single_device_game(data))


@worker.task(autoretry_for=(ConnectionError, TimeoutError), retry_backoff=True, max_retries=3)
def save_single_device_player(data: Dict[str, Any]) -> None:
    asyncio.run(__async_save_single_device_player(data))


@worker.task(autoretry_for=(ConnectionError, TimeoutError), retry_backoff=True, max_retries=3)
def save_multi_device_game(data: Dict[str, Any]) -> None:
    asyncio.run(__async_save_multi_device_game(data))


@worker.task(autoretry_for=(ConnectionError, TimeoutError), retry_backoff=True, max_retries=3)
def save_multi_device_player(data: Dict[str, Any]) -> None:
    asyncio.run(__async_save_multi_device_player(data))


@worker.task(autoretry_for=(ConnectionError, TimeoutError), retry_backoff=True, max_retries=3)
def clear_single_device_game(data: Dict[str, Any]) -> None:
    asyncio.run(__async_clear_single_device_game(data))


@worker.task(autoretry_for=(ConnectionError, TimeoutError), retry_backoff=True, max_retries=3)
def clear_single_device_player(data: Dict[str, Any]) -> None:
    asyncio.run(__async_clear_single_device_player(data))


@worker.task(autoretry_for=(ConnectionError, TimeoutError), retry_backoff=True, max_retries=3)
def clear_multi_device_game(data: Dict[str, Any]) -> None:
    asyncio.run(__async_clear_multi_device_game(data))


@worker.task(autoretry_for=(ConnectionError, TimeoutError), retry_backoff=True, max_retries=3)
def clear_multi_device_player(data: Dict[str, Any]) -> None:
    asyncio.run(__async_clear_multi_device_player(data))
