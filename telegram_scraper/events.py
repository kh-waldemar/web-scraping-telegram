"""Telethon event handlers for new messages."""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from telethon import events

from .config import Config
from .media import download_all_for_message
from .sender import send_batch_to_n8n, send_to_n8n
from .state import load_state, save_state
from .utils import format_reaction, sanitize_text

logger = logging.getLogger(__name__)


@dataclass
class AlbumBuffer:
    """Buffer for collecting album messages until debounce expires."""

    chat: str
    messages: List
    last_update: float = field(default_factory=time.time)


pending_albums: Dict[int, AlbumBuffer] = {}


def register_handlers(client, config: Config) -> None:
    """Register new message handler on the given client."""
    state: Dict[str, int] = load_state(config.state_file)
    target_chats = [f"@{c}" for c in config.channels]
    async def flush_albums() -> None:
        while True:
            now = time.time()
            to_flush = [
                gid for gid, buf in pending_albums.items()
                if now - buf.last_update >= config.album_debounce_sec
            ]
            for gid in to_flush:
                buf = pending_albums.pop(gid)
                await _process_album(buf)
            await asyncio.sleep(1)

    async def _process_album(buf: AlbumBuffer) -> None:
        messages = buf.messages
        first = messages[0]
        author_id: Optional[int] = None
        if getattr(first, "from_id", None) and hasattr(first.from_id, "user_id"):
            author_id = first.from_id.user_id  # type: ignore[assignment]

        payload = {
            "group": buf.chat,
            "author_id": author_id,
            "content": sanitize_text(first.message),
            "date": first.date.strftime("%Y-%m-%d %H:%M:%S"),
            "message_id": first.id,
            "author": first.post_author,
            "views": first.views,
            "reactions": " ".join(
                format_reaction(r) for r in getattr(first.reactions, "results", [])
            ),
            "shares": first.forwards,
            "media": True,
            "url": f"https://t.me/{buf.chat}/{first.id}",
            "comments_list": [],
            "album_group_id": getattr(first, "grouped_id", None),
            "has_media": True,
            "media_count": 0,
        }

        if config.media_download and config.media_send_mode == "multipart":
            file_items = []
            for m in messages:
                file_items.extend(
                    await download_all_for_message(
                        client, m, config.media_dir, config.media_max_mb
                    )
                )
            payload["media_count"] = len(file_items)
            send_batch_to_n8n(payload, file_items, config)
        else:
            payload["media_count"] = len(messages)
            send_to_n8n(payload, config)

    client.loop.create_task(flush_albums())

    @client.on(events.NewMessage(chats=target_chats))
    async def handler(event) -> None:  # type: ignore[override]
        chat = await event.get_chat()
        chat_username = getattr(chat, "username", None) or getattr(chat, "title", "")
        chat_username = chat_username.lstrip("@")
        last_id = state.get(chat_username)
        if last_id and event.message.id <= last_id:
            return

        msg = event.message
        state[chat_username] = msg.id
        save_state(config.state_file, state)

        grouped_id = getattr(msg, "grouped_id", None)
        if grouped_id:
            buf = pending_albums.get(grouped_id)
            if buf:
                buf.messages.append(msg)
                buf.last_update = time.time()
            else:
                pending_albums[grouped_id] = AlbumBuffer(
                    chat=chat_username, messages=[msg]
                )
            return

        author_id: Optional[int] = None
        if getattr(msg, "from_id", None) and hasattr(msg.from_id, "user_id"):
            author_id = msg.from_id.user_id  # type: ignore[assignment]

        has_media = bool(msg.media)
        payload = {
            "group": chat_username,
            "author_id": author_id,
            "content": sanitize_text(msg.message),
            "date": msg.date.strftime("%Y-%m-%d %H:%M:%S"),
            "message_id": msg.id,
            "author": msg.post_author,
            "views": msg.views,
            "reactions": " ".join(
                format_reaction(r) for r in getattr(msg.reactions, "results", [])
            ),
            "shares": msg.forwards,
            "media": has_media,
            "url": f"https://t.me/{chat_username}/{msg.id}",
            "comments_list": [],
            "album_group_id": None,
            "has_media": has_media,
            "media_count": 0,
        }

        if (
            config.media_download
            and has_media
            and config.media_send_mode == "multipart"
        ):
            file_items = await download_all_for_message(
                client, msg, config.media_dir, config.media_max_mb
            )
            payload["media_count"] = len(file_items)
            send_batch_to_n8n(payload, file_items, config)
        else:
            if has_media:
                payload["media_count"] = 1
            send_to_n8n(payload, config)

    logger.info("subscribed to %s", ",".join(config.channels))
