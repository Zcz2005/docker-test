from __future__ import annotations

import datetime as dt
import logging
import os
import re
import time
from typing import Any, Type

from db_utils import MySQLConnector

from .adb_manager import AdbManager
from .config import ScrcpyManagerConfig
from .device_pool import DevicePool
from .scrcpy_recorder import ScrcpyRecorder
from .task_loader import LoadedTask


logger = logging.getLogger(__name__)


class TaskThread:
    def __init__(
        self,
        device_pool: DevicePool,
        config: ScrcpyManagerConfig,
        loaded_task: LoadedTask,
    ):
        self.device_pool = device_pool
        self.config = config
        self.loaded_task = loaded_task
        self.adb_manager = AdbManager(config.paths, config.devices)

    def _is_device_connected(self, device_id: str) -> bool:
        return device_id in self.adb_manager.get_connected_devices()

    def _reconnect_device(self, device_id: str) -> bool:
        logger.info("任务[%s]：尝试重新连接设备 %s", self.loaded_task.name, device_id)
        if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}:\d+$", device_id):
            ip, port = device_id.split(":", 1)
            return self.adb_manager.connect_wifi_device(ip, int(port))
        self.adb_manager.disconnect_device(device_id)
        time.sleep(1)
        return self._is_device_connected(device_id)

    def run(self) -> None:
        logger.info("任务[%s]：等待空闲设备", self.loaded_task.name)
        device_id = self.device_pool.get_idle_device()
        logger.info("任务[%s]：获取设备 %s", self.loaded_task.name, device_id)

        video_path: str | None = None
        try:
            if not self._is_device_connected(device_id) and not self._reconnect_device(device_id):
                logger.error("任务[%s]：设备 %s 无法连接", self.loaded_task.name, device_id)
                return

            platform_task = self.loaded_task.task_class(device_id, *self.loaded_task.task_args)
            recorder = ScrcpyRecorder(
                device_id=device_id,
                paths=self.config.paths,
                recording=self.config.recording,
                task_id=self.loaded_task.task_id,
            )

            start_time = dt.datetime.fromtimestamp(int(time.time())).strftime("%Y-%m-%d %H:%M:%S")
            logger.info(
                "任务[%s]：设备 %s 开始录屏，最长等待 %s 秒",
                self.loaded_task.name,
                device_id,
                self.loaded_task.duration,
            )
            recording_success, task_success, video_path = recorder.run(
                duration=self.loaded_task.duration,
                external_task=platform_task,
            )

            if recording_success and task_success and video_path:
                end_time = dt.datetime.fromtimestamp(int(time.time())).strftime("%Y-%m-%d %H:%M:%S")
                with MySQLConnector(self.config.database) as db:
                    db.execute_update(
                        """
                        UPDATE tasktest
                        SET complete = 1, start_time = %s, end_time = %s, videopath = %s
                        WHERE id = %s
                        """,
                        (start_time, end_time, video_path, self.loaded_task.task_id),
                    )
                logger.info("任务[%s]：录制成功，videopath=%s", self.loaded_task.name, video_path)
            else:
                logger.warning(
                    "任务[%s]：失败 recording=%s task=%s，删除录像",
                    self.loaded_task.name,
                    recording_success,
                    task_success,
                )
                if video_path and os.path.exists(video_path):
                    os.remove(video_path)
        except Exception:
            logger.exception("任务[%s]：执行异常", self.loaded_task.name)
        finally:
            self.device_pool.release_device(device_id)
            logger.info("任务[%s]：释放设备 %s", self.loaded_task.name, device_id)
