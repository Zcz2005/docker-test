from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def _has_handler(logger: logging.Logger, handler_name: str) -> bool:
    return any(getattr(handler, "name", "") == handler_name for handler in logger.handlers)


def setup_logging(log_dir: Path, domain_id: str, level_name: str = "INFO") -> None:
    log_dir.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, level_name.upper(), logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not _has_handler(root_logger, "southnotary-console"):
        console_handler = logging.StreamHandler()
        console_handler.name = "southnotary-console"
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    file_handler_name = f"southnotary-file-{domain_id}"
    if not _has_handler(root_logger, file_handler_name):
        file_handler = TimedRotatingFileHandler(
            filename=str(log_dir / f"oos_uploader_{domain_id}.log"),
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.name = file_handler_name
        file_handler.suffix = "%Y-%m-%d.log"
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
