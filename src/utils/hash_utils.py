import hashlib
import logging
import traceback

logger = logging.getLogger(__name__)


def calculate_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()

    try:
        with open(file_path, "rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as exc:
        logger.error("计算文件哈希值失败: %s", exc)
        traceback.print_exc()
        raise
