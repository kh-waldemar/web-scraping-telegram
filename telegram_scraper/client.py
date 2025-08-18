"""Telethon client factory."""
from __future__ import annotations

from pathlib import Path
from telethon import TelegramClient


def get_client(api_id: int, api_hash: str) -> TelegramClient:
    """Create a Telethon client instance using a fixed session file."""
    session_path = Path("./sessions/zhito_admin")
    return TelegramClient(session_path, api_id, api_hash)
