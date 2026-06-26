"""Base class for platform-specific live room automation tasks."""

from __future__ import annotations

import logging
import time


logger = logging.getLogger(__name__)


class BasePlatformTask:
    def __init__(self, device_id: str, *args):
        self.device_id = device_id
        self.args = args

    def run_task(self) -> bool:
        raise NotImplementedError
