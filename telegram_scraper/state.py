"""Persistent state storage for last processed message IDs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


def load_state(path: str) -> Dict[str, int]:
    """Load state from a JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_state(path: str, state: Dict[str, int]) -> None:
    """Save state to a JSON file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh)
