from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

from .api import EvidenceApiClient
from .config import AppConfig
from .db_utils import MySQLConnector
from .env_loader import load_dotenv_if_available
from .logging_config import setup_logging
from .repository import TaskRepository
from .scheduler import ScheduledEvidenceThread
from .service import EvidenceTaskService
from .storage import OOSUploader


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Southnotary evidence polling and OOS upload service",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--once",
        choices=("fetch", "upload", "both"),
        help="Run one job cycle and exit instead of starting scheduled threads.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("run", "doctor"),
        default="run",
        help="Service command. Default is run.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output doctor results as JSON.",
    )
    return parser


def run_doctor(config: AppConfig, as_json: bool = False) -> int:
    checks: list[dict[str, Any]] = []

    def add_check(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    add_check("config", True, "Configuration loaded")

    try:
        with MySQLConnector(config.database) as db:
            db.execute_query("SELECT 1 AS ok")
        add_check("mysql", True, "Database connection successful")
    except Exception as exc:
        add_check("mysql", False, str(exc))

    try:
        repo = TaskRepository(config.database, config.domain_id)
        pending = repo.count_pending_upload()
        add_check("mysql_tasktest", True, f"Pending upload tasks: {pending}")
    except Exception as exc:
        add_check("mysql_tasktest", False, str(exc))

    try:
        import oos  # noqa: F401
        import ooscore  # noqa: F401
        add_check("oos_sdk", True, "CTYun OOS SDK import successful")
    except ImportError as exc:
        add_check("oos_sdk", False, str(exc))

    try:
        client = EvidenceApiClient(
            base_url=config.base_url,
            credentials=config.credentials,
            timeout_seconds=config.http_timeout_seconds,
            retry_count=config.api_retry_count,
            retry_backoff_seconds=config.api_retry_backoff_seconds,
            verify_ssl=config.verify_ssl,
        )
        token_result = client.get_token()
        add_check("api_token", True, f"Token acquired, expireAt={token_result.get('expireAt')}")
    except Exception as exc:
        add_check("api_token", False, str(exc))

    try:
        OOSUploader(config.storage)
        add_check("oos_client", True, f"OOS client initialized for bucket={config.storage.bucket}")
    except Exception as exc:
        add_check("oos_client", False, str(exc))

    all_ok = all(item["ok"] for item in checks)
    payload = {
        "ok": all_ok,
        "config": config.as_safe_dict(),
        "checks": checks,
    }

    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("Southnotary Uploader Doctor")
        print("=" * 40)
        for item in checks:
            status = "OK" if item["ok"] else "FAIL"
            print(f"[{status}] {item['name']}: {item['detail']}")
        print("=" * 40)
        print("RESULT:", "HEALTHY" if all_ok else "UNHEALTHY")

    return 0 if all_ok else 1


def main(argv: list[str] | None = None) -> int:
    load_dotenv_if_available()
    args = build_parser().parse_args(argv)

    if args.command == "doctor":
        config = AppConfig.from_env()
        setup_logging(config.log_dir, config.domain_id, config.log_level)
        return run_doctor(config, as_json=args.json)

    config = AppConfig.from_env()
    setup_logging(config.log_dir, config.domain_id, config.log_level)
    logging.info("=== 启动 [%s] 服务 ===", config.domain_id)

    service = EvidenceTaskService(config)

    if args.once == "fetch":
        service.evidence_api_worker()
        return 0
    if args.once == "upload":
        service.upload_completed_tasks()
        return 0
    if args.once == "both":
        service.evidence_api_worker()
        service.upload_completed_tasks()
        return 0

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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
