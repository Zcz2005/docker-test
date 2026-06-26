from __future__ import annotations

import argparse
import logging

from .config import AppConfig
from .logging_config import setup_logging
from .service import EvidenceTaskService, ScheduledEvidenceThread


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Southnotary evidence polling and OOS upload service")
    parser.add_argument(
        "--once",
        choices=("fetch", "upload", "both"),
        help="Run one job cycle and exit instead of starting scheduled threads.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = AppConfig.from_env()
    setup_logging(config.log_dir, config.domain_id, config.log_level)
    logging.info("=== 启动 [%s] 服务 ===", config.domain_id)

    service = EvidenceTaskService(config)

    if args.once == "fetch":
        service.evidence_api_worker()
        return
    if args.once == "upload":
        service.upload_completed_tasks()
        return
    if args.once == "both":
        service.evidence_api_worker()
        service.upload_completed_tasks()
        return

    evidence_thread = ScheduledEvidenceThread(
        task_func=service.evidence_api_worker,
        interval=config.evidence_fetch_interval_seconds,
        name="EvidenceDataThread",
    )
    upload_thread = ScheduledEvidenceThread(
        task_func=service.upload_completed_tasks,
        interval=config.upload_interval_seconds,
        name="OOSUploadThread",
    )

    evidence_thread.start()
    upload_thread.start()

    try:
        while evidence_thread.is_alive() or upload_thread.is_alive():
            evidence_thread.join(1)
            upload_thread.join(1)
    except KeyboardInterrupt:
        logging.info("接收到用户中断信号，正在停止所有定时线程...")
        evidence_thread.stop()
        upload_thread.stop()
        evidence_thread.join()
        upload_thread.join()
        logging.info("所有定时线程已停止，程序退出")


if __name__ == "__main__":
    main()
