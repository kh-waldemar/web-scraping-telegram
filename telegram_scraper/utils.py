"""Utility helpers for telegram_scraper."""
from __future__ import annotations

import logging
from typing import Optional


def format_reaction(r) -> str:
    """Format a Telethon reaction count safely."""
    return f"{getattr(getattr(r, 'reaction', None), 'emoticon', str(getattr(r, 'reaction', '')))} {r.count}"


def setup_logging(level: str) -> None:
    """Configure logging with a uniform format."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def sanitize_text(text: Optional[str]) -> str:
    """Basic text sanitizer removing null bytes."""
    if not text:
        return ""
    return text.replace("\x00", "")
