"""This module provides server app initialization."""

import os
import asyncio
import logging

from aiohttp.web import Application, run_app
from core.database.postgres import PoolManager as PGPoolManager
from core.database.redis import PoolManager as RedisPoolManager

from views import routes


LOG = logging.getLogger("")
LOG_FORMAT = "%(asctime)s - %(levelname)s: %(name)s: %(message)s"
ACCESS_LOG_FORMAT = "%a [VIEW: %r] [RESPONSE: %s (%bb)] [TIME: %Dms]"


def init_logging():
    """Initialize stream and file logger if it is available."""
    logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)

    log_dir = os.environ.get("LOG_DIR")
    log_filepath = f'{log_dir}/server.log'
    if log_dir and os.path.isfile(log_filepath) and os.access(log_filepath, os.W_OK):
        formatter = logging.Formatter(LOG_FORMAT)
        file_handler = logging.FileHandler(log_filepath)
        file_handler.setFormatter(formatter)
        logging.getLogger("").addHandler(file_handler)


async def init_clients(app):
    """Initialize application with clients."""
    app["postgres"] = postgres = await PGPoolManager.create()
    app["redis"] = redis = await RedisPoolManager.create()

    LOG.debug("Clients has successfully initialized.")

    yield

    await asyncio.gather(
        postgres.close(),
        redis.close()
    )
    LOG.debug("Clients has successfully closed.")


def main():
    """Create aiohttp web server and run it."""
    host = os.environ.get("SERVER_HOST", "localhost")
    port = os.environ.get("SERVER_PORT", 5000)

    app = Application()

    init_logging()
    app.add_routes(routes)
    app.cleanup_ctx.append(init_clients)

    run_app(
        app,
        host=host,
        port=port,
        access_log_format=ACCESS_LOG_FORMAT
    )


if __name__ == '__main__':
    main()