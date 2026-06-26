from __future__ import annotations

import datetime as dt
import logging
import sys
import time
from pathlib import Path


class BeijingTimeFormatter(logging.Formatter):
    converter = time.localtime

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            return time.strftime(datefmt, ct)
        base = time.strftime("%Y-%m-%d %H:%M:%S", ct)
        return f"{base},{int(record.msecs):03d}"


def get_time_based_log_filename(prefix: str = "app") -> str:
    return f"{prefix}_{dt.datetime.now().strftime('%Y%m%d%H')}.log"


def cleanup_old_files(directory: Path, *, days_to_keep: int, label: str) -> int:
    if not directory.exists():
        return 0

    cutoff_time = time.time() - (days_to_keep * 86400)
    deleted_count = 0

    for file_path in directory.iterdir():
        if not file_path.is_file():
            continue
        if file_path.stat().st_mtime >= cutoff_time:
            continue
        try:
            file_path.unlink()
            deleted_count += 1
            logging.info("已删除旧%s文件: %s", label, file_path.name)
        except OSError as exc:
            logging.error("删除%s文件失败 %s: %s", label, file_path.name, exc)

    if deleted_count:
        logging.info("%s清理完成，共删除 %s 个文件（保留最近 %s 天）", label, deleted_count, days_to_keep)
    return deleted_count


def setup_root_logging(log_dir: Path, prefix: str = "scrcpy_manager") -> str:
    log_dir.mkdir(parents=True, exist_ok=True)
    formatter = BeijingTimeFormatter("%(asctime)s - %(levelname)s - %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    log_filename = get_time_based_log_filename(prefix)
    file_handler = logging.FileHandler(log_dir / log_filename, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    return log_filename
