#!/usr/bin/env python3
"""Validate required environment variables before starting the service."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from southnotary_uploader.env_loader import load_dotenv_if_available


REQUIRED_VARS = [
    "SOUTHNOTARY_APPID",
    "SOUTHNOTARY_RANDKEY",
    "SOUTHNOTARY_HASHVAL",
    "OOS_ACCESS_KEY",
    "OOS_SECRET_KEY",
    "MYSQL_HOST",
    "MYSQL_USER",
    "MYSQL_PASSWORD",
    "MYSQL_DATABASE",
]

OPTIONAL_VARS = [
    "SOUTHNOTARY_DOMAIN_ID",
    "SOUTHNOTARY_BASE_URL",
    "SOUTHNOTARY_API_HOST",
    "OOS_ENDPOINT",
    "OOS_BUCKET",
    "OOS_OBJECT_KEY_PREFIX",
    "EVIDENCE_FETCH_INTERVAL_SECONDS",
    "UPLOAD_INTERVAL_SECONDS",
    "HTTP_TIMEOUT_SECONDS",
    "LOG_LEVEL",
    "LOG_DIR",
]


def main() -> int:
    load_dotenv_if_available()
    missing = [name for name in REQUIRED_VARS if not os.getenv(name)]
    if missing:
        print("Missing required environment variables:")
        for name in missing:
            print(f"  - {name}")
        return 1

    print("Required environment variables: OK")
    print("\nEffective configuration:")
    for name in REQUIRED_VARS + OPTIONAL_VARS:
        value = os.getenv(name)
        if value is None:
            continue
        if any(secret in name for secret in ("PASSWORD", "SECRET", "HASHVAL", "TOKEN", "KEY")):
            display = "<set>"
        else:
            display = value
        print(f"  {name}={display}")

    try:
        import oos  # noqa: F401
        import ooscore  # noqa: F401
        print("\nCTYun OOS SDK: OK")
    except ImportError:
        print("\nCTYun OOS SDK: NOT INSTALLED (required for upload)")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
