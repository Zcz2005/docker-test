"""Object key builder for OOS uploads."""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

from .constants import DEFAULT_OBJECT_KEY_PREFIX


def build_object_key(
    video_path: str | Path,
    *,
    prefix: str = DEFAULT_OBJECT_KEY_PREFIX,
    now: dt.datetime | None = None,
) -> str:
    current = now or dt.datetime.now()
    today = current.strftime("%Y-%m-%d")
    timestamp = int(current.timestamp())
    filename = os.path.basename(str(video_path))
    normalized_prefix = prefix.strip("/")
    return f"{normalized_prefix}/{today}/{timestamp}/{filename}"
