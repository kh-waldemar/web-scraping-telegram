"""Telethon client factory."""
from __future__ import annotations

from pathlib import Path
from telethon import TelegramClient


def get_client(username: str, api_id: int, api_hash: str) -> TelegramClient:
    """Create a Telethon client instance."""
    session_path = Path("./sessions") / username
    return TelegramClient(session_path, api_id, api_hash)
