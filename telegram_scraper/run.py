"""Entry point for running the Telegram scraper."""
from __future__ import annotations

import asyncio
import logging
import time

from .client import get_client
from .config import load_config
from .events import register_handlers
from .utils import setup_logging


async def _runner() -> None:
    config = load_config()
    setup_logging(config.log_level)
    client = get_client(config.username, config.api_id, config.api_hash)
    await client.start(phone=config.phone)
    register_handlers(client, config)
    logging.getLogger(__name__).info("listening on %s", ",".join(config.channels))
    await client.run_until_disconnected()


def main() -> None:
    while True:
        try:
            asyncio.run(_runner())
        except KeyboardInterrupt:
            break
        except Exception as exc:  # pragma: no cover - network errors etc.
            logging.getLogger(__name__).exception("scraper crashed: %s", exc)
            time.sleep(5)


if __name__ == "__main__":
    main()
