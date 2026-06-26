import logging
from logging.handlers import TimedRotatingFileHandler

from src.config import DOMAIN_ID, LOG_DIR, LOG_LEVEL


def setup_logging() -> None:
    log_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    if not root_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        root_logger.addHandler(console_handler)

        file_handler = TimedRotatingFileHandler(
            filename=LOG_DIR / f"oos_uploader_{DOMAIN_ID}.log",
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.suffix = "%Y-%m-%d.log"
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)
