"""Optional .env loading helpers."""

from __future__ import annotations

import logging
import os
from pathlib import Path


logger = logging.getLogger(__name__)


def load_dotenv_if_available(dotenv_path: str | Path | None = None) -> bool:
    """Load .env when python-dotenv is installed.

    Search order:
    1. DOTENV_PATH environment variable
    2. explicit dotenv_path argument
    3. ./.env from current working directory
    4. <project-root>/.env
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False

    candidates: list[Path] = []
    env_override = os.getenv("DOTENV_PATH")
    if env_override:
        candidates.append(Path(env_override))
    if dotenv_path is not None:
        candidates.append(Path(dotenv_path))
    candidates.append(Path.cwd() / ".env")
    candidates.append(Path(__file__).resolve().parent.parent / ".env")

    for candidate in candidates:
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            logger.debug("Loaded dotenv file: %s", candidate)
            return True

    return False
