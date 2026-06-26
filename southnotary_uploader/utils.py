"""Small helper utilities."""

from __future__ import annotations

import datetime as dt
import logging
import re
from typing import Any

from .constants import SUCCESS_API_CODE


logger = logging.getLogger(__name__)


def is_success_code(code: Any) -> bool:
    return str(code) == SUCCESS_API_CODE


def format_datetime(value: Any) -> str:
    if isinstance(value, dt.datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return "" if value is None else str(value)


def extract_xiuse_room_id(room_id: Any, url: str, task_id: str) -> Any:
    if str(room_id) != "0":
        return room_id

    match = re.search(r"\d+$", url or "")
    if not match:
        return room_id

    extracted_room_id = match.group(0)
    logger.info("任务[%s]：Xiuse平台roomId为0，从URL提取新roomId: %s", task_id, extracted_room_id)
    return extracted_room_id
