"""Telethon client factory."""
from __future__ import annotations

from telethon import TelegramClient


def get_client(username: str, api_id: int, api_hash: str) -> TelegramClient:
    """Create a Telethon client instance."""
    return TelegramClient(username, api_id, api_hash)
