import argparse
import asyncio
import logging
from typing import AsyncIterator

from telethon.tl.types import Message

from .client import get_client
from .config import Config, load_config
from .media import download_all_for_message
from .sender import send_batch_to_n8n, send_to_n8n
from .utils import format_reaction, sanitize_text, setup_logging

log = logging.getLogger(__name__)


async def iter_thread_messages(client, chat: str, thread_msg_id: int) -> AsyncIterator[Message]:
    async for m in client.iter_messages(chat, reply_to=thread_msg_id, reverse=True):
        yield m


async def scrape_thread(config: Config, delay: float) -> None:
    if not config.thread_message_id:
        raise ValueError("THREAD_MESSAGE_ID is not set; please add it to .env")

    async with get_client(config.api_id, config.api_hash) as client:
        async def _send_group(messages, chat_name):
            first = messages[0]
            has_media = any(bool(m.media) for m in messages)
            data = {
                "group": chat_name.lstrip("@"),
                "author_id": first.sender_id,
                "content": sanitize_text(first.text or ""),
                "date": first.date.strftime("%Y-%m-%d %H:%M:%S") if first.date else "",
                "message_id": first.id,
                "author": getattr(first, "post_author", None),
                "views": getattr(first, "views", None),
                "reactions": " ".join(
                    format_reaction(r) for r in getattr(first.reactions, "results", [])
                ),
                "shares": getattr(first, "forwards", None),
                "media": has_media,
                "url": f"https://t.me/{chat_name.lstrip('@')}/{first.id}",
                "comments_list": [],
                "thread_message_id": config.thread_message_id,
                "mode": "bulk_thread_export",
                "album_group_id": getattr(first, "grouped_id", None),
                "has_media": has_media,
                "media_count": 0,
            }
            if (
                config.media_download
                and has_media
                and config.media_send_mode == "multipart"
            ):
                file_items = []
                for m in messages:
                    file_items.extend(
                        await download_all_for_message(
                            client, m, config.media_dir, config.media_max_mb
                        )
                    )
                data["media_count"] = len(file_items)
                send_batch_to_n8n(data, file_items, config)
            else:
                if has_media:
                    data["media_count"] = len(messages)
                send_to_n8n(data, config)

        for chat in config.channels:
            log.info(f"scraping thread {config.thread_message_id} in {chat}")
            current_gid = None
            pending = []
            async for msg in iter_thread_messages(client, chat, config.thread_message_id):
                gid = getattr(msg, "grouped_id", None)
                if gid:
                    if current_gid is None or gid == current_gid:
                        current_gid = gid
                        pending.append(msg)
                        continue
                    await _send_group(pending, chat)
                    await asyncio.sleep(delay)
                    pending = [msg]
                    current_gid = gid
                else:
                    if pending:
                        await _send_group(pending, chat)
                        await asyncio.sleep(delay)
                        pending = []
                        current_gid = None
                    await _send_group([msg], chat)
                    await asyncio.sleep(delay)
            if pending:
                await _send_group(pending, chat)
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
