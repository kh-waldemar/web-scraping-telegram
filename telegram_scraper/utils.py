"""Utility helpers for telegram_scraper."""
from __future__ import annotations

import logging
from typing import Optional


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
