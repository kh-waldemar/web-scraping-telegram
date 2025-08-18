"""Configuration loading for telegram_scraper."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List
import os

from dotenv import load_dotenv


@dataclass
class Config:
    api_id: int
    api_hash: str
    channels: List[str]
    webhook_url: str
    http_timeout: int
    http_max_retries: int
    http_backoff_seconds: int
    log_level: str
    state_backend: str
    state_file: str
    thread_message_id: int | None
    media_download: bool
    media_dir: str
    media_max_mb: int
    media_send_mode: str
    album_debounce_sec: int


def _require(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise ValueError(f"Environment variable {name} is required")
    return value


def load_config(env_file: str = ".env") -> Config:
    """Load configuration from environment variables."""
    load_dotenv(env_file)

    channels = [c.strip().lstrip("@") for c in _require("TG_CHANNELS").split(",") if c.strip()]

    thread_env = os.getenv("THREAD_MESSAGE_ID")
    thread_message_id = int(thread_env) if thread_env else None

    config = Config(
        api_id=int(_require("TG_API_ID")),
        api_hash=_require("TG_API_HASH"),
        channels=channels,
        webhook_url=_require("N8N_WEBHOOK_URL"),
        http_timeout=int(os.getenv("HTTP_TIMEOUT", "10")),
        http_max_retries=int(os.getenv("HTTP_MAX_RETRIES", "5")),
        http_backoff_seconds=int(os.getenv("HTTP_BACKOFF_SECONDS", "2")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        state_backend=os.getenv("STATE_BACKEND", "file"),
        state_file=os.getenv("STATE_FILE", ".state.json"),
        thread_message_id=thread_message_id,
        media_download=os.getenv("MEDIA_DOWNLOAD", "1") == "1",
        media_dir=os.getenv("MEDIA_DIR", "./data/media"),
        media_max_mb=int(os.getenv("MEDIA_MAX_MB", "50")),
        media_send_mode=os.getenv("MEDIA_SEND_MODE", "multipart").lower(),
        album_debounce_sec=int(os.getenv("ALBUM_DEBOUNCE_SEC", "2")),
    )

    os.makedirs(config.media_dir, exist_ok=True)
    return config
