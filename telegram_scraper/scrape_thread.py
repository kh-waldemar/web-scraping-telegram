import argparse
import asyncio
import logging
from typing import AsyncIterator

from telethon.tl.types import Message

from .client import get_client
from .config import Config, load_config
from .sender import send_to_n8n
from .utils import sanitize_text, setup_logging

log = logging.getLogger(__name__)


async def iter_thread_messages(client, chat: str, thread_msg_id: int) -> AsyncIterator[Message]:
    async for m in client.iter_messages(chat, reply_to=thread_msg_id, reverse=True):
        yield m


async def scrape_thread(config: Config, delay: float) -> None:
    if not config.thread_message_id:
        raise ValueError("THREAD_MESSAGE_ID is not set; please add it to .env")

    async with get_client(config.api_id, config.api_hash) as client:
        for chat in config.channels:
            log.info(f"scraping thread {config.thread_message_id} in {chat}")
            async for msg in iter_thread_messages(client, chat, config.thread_message_id):
                data = {
                    "group": chat.lstrip("@"),
                    "author_id": msg.sender_id,
                    "content": sanitize_text(msg.text or ""),
                    "date": msg.date.strftime("%Y-%m-%d %H:%M:%S") if msg.date else "",
                    "message_id": msg.id,
                    "author": getattr(msg, "post_author", None),
                    "views": getattr(msg, "views", None),
                    "reactions": " ".join(
                        f"{r.emoticon} {r.count}" for r in getattr(msg.reactions, "results", [])
                    ),
                    "shares": getattr(msg, "forwards", None),
                    "media": bool(msg.media),
                    "url": f"https://t.me/{chat.lstrip('@')}/{msg.id}",
                    "comments_list": [],
                    "thread_message_id": config.thread_message_id,
                    "mode": "bulk_thread_export",
                }
                send_to_n8n(data, config)
                await asyncio.sleep(delay)
            log.info(f"done thread {config.thread_message_id} in {chat}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--delay",
        type=float,
        default=3,
        help="Delay between sending messages to the webhook in seconds",
    )
    args = parser.parse_args()

    config = load_config()
    setup_logging(config.log_level)
    asyncio.run(scrape_thread(config, args.delay))


if __name__ == "__main__":
    main()
