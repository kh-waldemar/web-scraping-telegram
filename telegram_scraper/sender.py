"""HTTP sender to forward messages to n8n webhook."""
from __future__ import annotations

import json
import logging
import os
import time
from contextlib import ExitStack
from typing import Dict, List, Tuple

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


def send_batch_to_n8n(
    data: Dict, file_items: List[Tuple[str, str | None]], config: Config
) -> None:
    """Send ``data`` and ``file_items`` to n8n in a single request.

    If ``file_items`` is empty the call falls back to ``send_to_n8n``. When
    files are present they are sent as ``files[]`` fields in multipart/form-data
    together with a ``payload`` field containing JSON metadata. The request uses
    the same retry/backoff logic as :func:`send_to_n8n`.
    """

    items = list(file_items)
    if not items:
        send_to_n8n(data, config)
        return

    for attempt in range(1, config.http_max_retries + 1):
        try:
            with ExitStack() as stack:
                files = []
                for path, mimetype in items:
                    fh = stack.enter_context(open(path, "rb"))
                    files.append(
                        (
                            "files[]",
                            (
                                os.path.basename(path),
                                fh,
                                mimetype or "application/octet-stream",
                            ),
                        )
                    )
                response = requests.post(
                    config.webhook_url,
                    files=files,
                    data={"payload": json.dumps(data)},
                    timeout=config.http_timeout,
                )
            if response.ok:
                logger.info(
                    "sent batch %s with %s file(s) and payload",
                    data.get("message_id"),
                    len(items),
                )
                return
            logger.warning(
                "webhook responded with %s: %s", response.status_code, response.text
            )
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("error sending batch webhook: %s", exc)
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
