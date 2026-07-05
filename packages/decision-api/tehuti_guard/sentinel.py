"""Fetch Sentinel `unified_view` for a machine_id."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def default_sentinel_base() -> str:
    return os.environ.get("TEHUTI_GUARD_SENTINEL_URL", "http://127.0.0.1:4242").rstrip("/")


def fetch_unified_view(machine_id: str, base_url: str | None = None) -> dict[str, Any] | None:
    base = (base_url or default_sentinel_base()).rstrip("/")
    path = urllib.parse.quote(machine_id, safe="")
    url = f"{base}/status/{path}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode("utf-8")
            data = json.loads(raw)
            return data if isinstance(data, dict) else None
    except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError):
        return None
