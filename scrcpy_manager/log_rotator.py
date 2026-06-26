from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from .logging_setup import BeijingTimeFormatter, get_time_based_log_filename


class HourlyLogRotator:
    def __init__(self, log_dir: Path, prefix: str = "scrcpy_manager"):
        self.log_dir = log_dir
        self.prefix = prefix
        self.current_filename = get_time_based_log_filename(prefix)
        self.last_update = time.time()

    def maybe_rotate(self, update_interval: int) -> None:
        now = time.time()
        if now - self.last_update < update_interval:
            return

        new_filename = get_time_based_log_filename(self.prefix)
        self.last_update = now
        if new_filename == self.current_filename:
            return

        formatter = BeijingTimeFormatter("%(asctime)s - %(levelname)s - %(message)s")
        new_handler = logging.FileHandler(self.log_dir / new_filename, encoding="utf-8")
        new_handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.FileHandler) and handler.stream is not sys.stdout:
                root_logger.removeHandler(handler)
                handler.close()
        root_logger.addHandler(new_handler)
        self.current_filename = new_filename
        logging.info("日志文件已更新为: %s", new_filename)
