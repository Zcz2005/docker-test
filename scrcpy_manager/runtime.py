from __future__ import annotations

import datetime as dt
import logging
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .adb_manager import AdbManager
from .config import ScrcpyManagerConfig
from .device_pool import DevicePool
from .log_rotator import HourlyLogRotator
from .task_loader import fetch_tasks_from_db
from .task_runner import TaskThread


logger = logging.getLogger(__name__)


class RuntimeController:
    def __init__(self, config: ScrcpyManagerConfig):
        self.config = config
        self.running = True
        self._log_rotator = HourlyLogRotator(config.paths.logs)
        self._last_log_cleanup = time.time()
        self._last_recording_cleanup_date = dt.datetime.now().date()
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame) -> None:
        logger.info("收到信号 %s，准备退出...", signum)
        self.running = False

    def _maintenance(self) -> None:
        now = time.time()
        if now - self._last_log_cleanup >= self.config.system.log_cleanup_interval:
            cleanup_old_files(
                self.config.paths.logs,
                days_to_keep=self.config.system.log_retention_days,
                label="日志",
            )
            self._last_log_cleanup = now

        current_date = dt.datetime.now().date()
        if current_date > self._last_recording_cleanup_date:
            cleanup_old_files(
                self.config.paths.recordings,
                days_to_keep=self.config.system.recording_retention_days,
                label="录屏",
            )
            self._last_recording_cleanup_date = current_date

        self._log_rotator.maybe_rotate(self.config.system.log_update_interval)

    def _discover_devices(self) -> list[str]:
        adb_manager = AdbManager(self.config.paths, self.config.devices)
        devices = adb_manager.setup_wifi_devices()
        if devices:
            return devices
        return adb_manager.get_connected_devices()

    def run_forever(self) -> None:
        logger.info("启动 scrcpy 任务处理系统 (domain=%s)", self.config.system.domain_id)
        while self.running:
            try:
                self._maintenance()
                device_list = self._discover_devices()
                if not device_list:
                    logger.info("未发现设备，%s 秒后重试", self.config.system.check_interval)
                    time.sleep(self.config.system.check_interval)
                    continue

                logger.info("已连接设备: %s", device_list)
                device_pool = DevicePool(device_list)
                tasks = fetch_tasks_from_db(self.config)
                if not tasks:
                    logger.info("当前没有待录制任务")
                    time.sleep(self.config.system.check_interval)
                    continue

                logger.info("发现 %s 个任务，并发上限=%s", len(tasks), device_pool.size)
                with ThreadPoolExecutor(max_workers=device_pool.size) as executor:
                    futures = [
                        executor.submit(
                            TaskThread(device_pool, self.config, loaded_task).run
                        )
                        for loaded_task in tasks
                    ]
                    for future in as_completed(futures):
                        if not self.running:
                            break
                        future.result()

                logger.info("当前批次 %s 个任务处理完成", len(tasks))
            except Exception:
                logger.exception("主循环异常")
                for _ in range(self.config.system.error_wait):
                    if not self.running:
                        break
                    time.sleep(1)

        logger.info("scrcpy 任务处理系统已停止")
