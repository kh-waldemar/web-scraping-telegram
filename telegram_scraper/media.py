"""Helpers for downloading media files from Telegram messages."""
from __future__ import annotations

import logging
import os
from typing import AsyncIterator, Dict, Optional

from telethon.tl.custom.message import Message

logger = logging.getLogger(__name__)


async def download_one(
    client, msg: Message, download_dir: str, max_mb: int
) -> Optional[Dict]:
    """Download a single media item from ``msg`` into ``download_dir``.

    Returns metadata about the downloaded file or ``None`` if the file is
    missing or exceeds the size limit.
    """
    if not msg.media:
        return None

    file = getattr(msg, "file", None)
    if file and getattr(file, "size", 0) > max_mb * 1024 * 1024:
        logger.warning("media larger than %sMB, skipping", max_mb)
        return None

    try:
        path = await client.download_media(msg, download_dir)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("error downloading media: %s", exc)
        return None

    if not path or not os.path.exists(path):
        return None

    filesize = os.path.getsize(path)
    if filesize > max_mb * 1024 * 1024:
        logger.warning("downloaded media larger than %sMB, skipping", max_mb)
        try:
            os.remove(path)
        except OSError:
            pass
        return None

    filename = os.path.basename(path)
    mimetype = getattr(file, "mime_type", None) if file else None
    return {
        "file_path": path,
        "filename": filename,
        "mimetype": mimetype,
        "filesize": filesize,
    }


async def iter_media_items(
    client, msg: Message, download_dir: str, max_mb: int
) -> AsyncIterator[Dict]:
    """Yield metadata dictionaries for each media item in ``msg``."""
    meta = await download_one(client, msg, download_dir, max_mb)
    if meta:
        yield meta
