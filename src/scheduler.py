import logging
import threading
import time
from typing import Callable, Optional

from src.config import DOMAIN_ID

logger = logging.getLogger(__name__)


class ScheduledEvidenceThread(threading.Thread):
    """Run a task function on a fixed interval in a background thread."""

    def __init__(
        self,
        task_func: Callable[[], None],
        interval: int = 300,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or "EvidenceScheduledThread", daemon=True)
        self.task_func = task_func
        self.interval = interval
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()
        logger.info("线程 %s 已收到停止信号，将在当前周期结束后退出", self.name)

    def run(self) -> None:
        logger.info(
            "[%s] 定时线程[%s]已启动，将每%s秒执行一次",
            DOMAIN_ID,
            self.name,
            self.interval,
        )
        while not self._stop_event.is_set():
            try:
                self.task_func()
            except Exception as exc:
                logger.error(
                    "[%s] 定时线程[%s]执行任务时发生未捕获异常: %s",
                    DOMAIN_ID,
                    self.name,
                    exc,
                    exc_info=True,
                )

            for _ in range(self.interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)
