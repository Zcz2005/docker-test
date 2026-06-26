from __future__ import annotations

import logging
import threading
from typing import Dict


logger = logging.getLogger(__name__)


class DevicePool:
    """Blocking pool that hands out one idle Android device at a time."""

    def __init__(self, device_ids: list[str]):
        self._device_map: Dict[str, bool] = {device_id: True for device_id in device_ids}
        self._condition = threading.Condition()

    def get_idle_device(self) -> str:
        with self._condition:
            while True:
                for device_id, is_idle in self._device_map.items():
                    if is_idle:
                        self._device_map[device_id] = False
                        return device_id
                self._condition.wait()

    def release_device(self, device_id: str) -> None:
        with self._condition:
            if device_id in self._device_map:
                self._device_map[device_id] = True
                self._condition.notify()

    @property
    def size(self) -> int:
        return len(self._device_map)
