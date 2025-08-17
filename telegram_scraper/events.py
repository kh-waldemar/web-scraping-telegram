"""Telethon event handlers for new messages."""
from __future__ import annotations

import logging
from typing import Dict, Optional

from telethon import events

from .config import Config
from .sender import send_to_n8n
from .state import load_state, save_state
from .utils import sanitize_text

logger = logging.getLogger(__name__)


def register_handlers(client, config: Config) -> None:
    """Register new message handler on the given client."""
    state: Dict[str, int] = load_state(config.state_file)
    target_chats = [f"@{c}" for c in config.channels]

    @client.on(events.NewMessage(chats=target_chats))
    async def handler(event) -> None:  # type: ignore[override]
        chat = await event.get_chat()
        chat_username = getattr(chat, "username", None) or getattr(chat, "title", "")
        chat_username = chat_username.lstrip("@")
        last_id = state.get(chat_username)
        if last_id and event.message.id <= last_id:
            return

        msg = event.message
        author_id: Optional[int] = None
        if getattr(msg, "from_id", None) and hasattr(msg.from_id, "user_id"):
            author_id = msg.from_id.user_id  # type: ignore[assignment]

        payload = {
            "group": chat_username,
            "author_id": author_id,
            "content": sanitize_text(msg.message),
            "date": msg.date.strftime("%Y-%m-%d %H:%M:%S"),
            "message_id": msg.id,
            "author": msg.post_author,
            "views": msg.views,
            "reactions": " ".join(
                f"{r.emoticon} {r.count}" for r in getattr(msg.reactions, "results", [])
            ),
            "shares": msg.forwards,
            "media": msg.media is not None,
            "url": f"https://t.me/{chat_username}/{msg.id}",
            "comments_list": [],
        }

        state[chat_username] = msg.id
        save_state(config.state_file, state)
        send_to_n8n(payload, config)

    logger.info("subscribed to %s", ",".join(config.channels))
