import logging

from src.config import EVIDENCE_POLL_INTERVAL, UPLOAD_POLL_INTERVAL
from src.logging_config import setup_logging
from src.scheduler import ScheduledEvidenceThread
from src.workers.evidence_worker import evidence_api_worker
from src.workers.upload_worker import upload_completed_tasks

logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()
    logger.info("=== 启动 southnotary 取证上传服务 ===")

    evidence_thread = ScheduledEvidenceThread(
        task_func=evidence_api_worker,
        interval=EVIDENCE_POLL_INTERVAL,
        name="EvidenceDataThread",
    )
    upload_thread = ScheduledEvidenceThread(
        task_func=upload_completed_tasks,
        interval=UPLOAD_POLL_INTERVAL,
        name="OOSUploadThread",
    )

    evidence_thread.start()
    upload_thread.start()

    try:
        while evidence_thread.is_alive() or upload_thread.is_alive():
            evidence_thread.join(1)
            upload_thread.join(1)
    except KeyboardInterrupt:
        logger.info("接收到用户中断信号，正在停止所有定时线程...")
        evidence_thread.stop()
        upload_thread.stop()
        evidence_thread.join()
        upload_thread.join()
        logger.info("所有定时线程已停止，程序退出")


if __name__ == "__main__":
    main()
