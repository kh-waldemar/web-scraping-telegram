"""HTTP sender to forward messages to n8n webhook."""
from __future__ import annotations

import json
import logging
import time
from typing import Dict

import requests

from .config import Config

logger = logging.getLogger(__name__)


def send_to_n8n(data: Dict, config: Config) -> None:
    """Send data to the configured n8n webhook with retry/backoff."""
    for attempt in range(1, config.http_max_retries + 1):
        try:
            response = requests.post(
                config.webhook_url, json=data, timeout=config.http_timeout
            )
            if response.ok:
                logger.info("sent message %s", data.get("message_id"))
                return
            logger.warning("webhook responded with %s: %s", response.status_code, response.text)
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("error sending webhook: %s", exc)
        time.sleep(config.http_backoff_seconds * attempt)


def send_file_to_n8n(
    data: Dict, file_path: str, filename: str, mimetype: str | None, config: Config
) -> None:
    """Send a file with accompanying payload to n8n via multipart/form-data."""
    for attempt in range(1, config.http_max_retries + 1):
        try:
            with open(file_path, "rb") as fh:
                files = {
                    "file": (filename, fh, mimetype or "application/octet-stream"),
                }
                payload = {"payload": json.dumps(data)}
                response = requests.post(
                    config.webhook_url,
                    files=files,
                    data=payload,
                    timeout=config.http_timeout,
                )
            if response.ok:
                logger.info("sent file %s", filename)
                return
            logger.warning(
                "webhook responded with %s: %s", response.status_code, response.text
            )
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("error sending file webhook: %s", exc)
        time.sleep(config.http_backoff_seconds * attempt)
