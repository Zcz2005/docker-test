from __future__ import annotations

import datetime as dt
import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Callable

from .api import EvidenceApiClient, is_success_code
from .config import AppConfig, PLATFORM_MAP
from .db_utils import MySQLConnector
from .storage import OOSUploader, calculate_sha256


logger = logging.getLogger(__name__)


def _format_datetime(value: Any) -> str:
    if isinstance(value, dt.datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return "" if value is None else str(value)


def _extract_xiuse_room_id(room_id: Any, url: str, task_id: str) -> Any:
    if str(room_id) != "0":
        return room_id

    match = re.search(r"\d+$", url or "")
    if not match:
        return room_id

    extracted_room_id = match.group(0)
    logger.info("任务[%s]：Xiuse平台roomId为0，从URL提取新roomId: %s", task_id, extracted_room_id)
    return extracted_room_id


class EvidenceTaskService:
    def __init__(self, config: AppConfig):
        self.config = config

    def _new_api_client_with_token(self) -> EvidenceApiClient:
        evidence_client = EvidenceApiClient(
            base_url=self.config.base_url,
            credentials=self.config.credentials,
            timeout_seconds=self.config.http_timeout_seconds,
        )
        evidence_client.get_token()
        return evidence_client

    def upload_completed_tasks(self) -> None:
        evidence_client = self._new_api_client_with_token()
        uploader = OOSUploader(self.config.storage)

        with MySQLConnector(self.config.database) as db:
            completed_tasks = db.execute_query(
                """
                SELECT *
                FROM tasktest
                WHERE complete = 1 AND upload = 0 AND domain = %s
                """,
                (self.config.domain_id,),
            )

        logger.info("共查询到 %s 个已完成的任务", len(completed_tasks))

        for task in completed_tasks:
            self._upload_one_completed_task(task, evidence_client, uploader)

        print(f"=== [{self.config.domain_id}] 所有已完成任务的视频文件上传完成 ===")

    def _upload_one_completed_task(
        self,
        task: dict[str, Any],
        evidence_client: EvidenceApiClient,
        uploader: OOSUploader,
    ) -> None:
        task_db_id = task.get("id", "")
        task_id = task.get("taskid", "")
        video_path = task.get("videopath", "")

        if not video_path:
            logger.warning("任务[%s]：videopath为空，跳过上传", task_id)
            return

        if not Path(video_path).exists():
            logger.error("任务[%s]：文件不存在，跳过上传: %s", task_id, video_path)
            return

        logger.info("任务[%s]：开始计算文件哈希值: %s", task_id, video_path)
        file_hash = calculate_sha256(video_path)
        logger.info("任务[%s]：文件哈希值计算完成: %s", task_id, file_hash)

        now = dt.datetime.now()
        today = now.strftime("%Y-%m-%d")
        timestamp = int(now.timestamp())
        object_key = f"evidenceProd/Casefile/File/{today}/{timestamp}/{os.path.basename(video_path)}"

        logger.info("任务[%s]：开始上传文件到OOS: %s -> %s", task_id, video_path, object_key)
        response = uploader.upload_file(
            local_file_path=video_path,
            object_key=object_key,
            storage_class="STANDARD",
            content_type="video/mp4",
        )
        if not response:
            logger.error("任务[%s]：文件上传响应异常，未更新数据库", task_id)
            return

        logger.info("任务[%s]：文件上传成功！taskId=%s, objectKey=%s", task_id, task_id, object_key)

        status_code, response_text, response_json = evidence_client.upload_automated_forensics_file(
            obs_path=object_key,
            case_num=task.get("casenum", ""),
            task_id=task_id,
            screen_start_time=_format_datetime(task.get("start_time", "")),
            screen_end_time=_format_datetime(task.get("end_time", "")),
            file_hash=file_hash,
        )

        print("\n" + "=" * 50)
        print(f"响应内容：\n{response_text}")
        print("=" * 50 + "\n")

        if status_code != 200:
            logger.error("任务[%s]：接口返回非200状态码！状态码：%s，响应：%s", task_id, status_code, response_text)
            return

        if response_json is None:
            logger.error("任务[%s]：接口响应非JSON格式，无法解析！响应：%s", task_id, response_text)
            return

        business_code = response_json.get("code", -1)
        message = response_json.get("message", "无错误信息")
        terminal_messages = {"取证任务已结束！", "取证任务不存在！"}

        if str(business_code) == "500" and message in terminal_messages:
            logger.info("任务[%s]：%s，直接更新数据库", task_id, message)
            self._mark_task_uploaded(task_db_id, task_id)
            return

        if not is_success_code(business_code):
            logger.error(
                "任务[%s]：接口业务处理失败！业务code：%s，错误信息：%s，响应：%s",
                task_id,
                business_code,
                message,
                response_text,
            )
            return

        self._mark_task_uploaded(task_db_id, task_id)

    def _mark_task_uploaded(self, task_db_id: Any, task_id: str) -> None:
        try:
            with MySQLConnector(self.config.database) as db:
                db.execute_update("UPDATE tasktest SET upload = 1 WHERE id = %s", (task_db_id,))
            logger.info("任务[%s]：数据库更新成功，id=%s的upload字段已设为1", task_id, task_db_id)
        except Exception:
            logger.exception("任务[%s]：数据库更新失败，id=%s", task_id, task_db_id)

    def evidence_api_worker(self) -> None:
        evidence_client = self._new_api_client_with_token()
        response = evidence_client.get_automated_forensics()
        evidence_client.pretty_print(response)

        if not is_success_code(response.get("code")):
            logger.error("[%s] 取证接口返回非成功code: %s", self.config.domain_id, response)
            return

        forensic_data_list = response.get("data")
        if not isinstance(forensic_data_list, list) or not forensic_data_list:
            return

        insert_count = 0
        skip_count = 0

        for forensic_data in forensic_data_list:
            task_id = forensic_data.get("taskId", "")
            if not task_id:
                skip_count += 1
                logger.warning("taskId为空，跳过数据入库")
                continue

            try:
                inserted = self._insert_forensic_task_if_needed(forensic_data)
                if inserted:
                    insert_count += 1
                    logger.info(
                        "任务[%s]：取证数据插入成功！taskId=%s, url=%s",
                        task_id,
                        task_id,
                        forensic_data.get("url", ""),
                    )
                else:
                    skip_count += 1
            except Exception:
                skip_count += 1
                logger.exception("任务[%s]：处理失败（查询/插入异常）", task_id)

        logger.info(
            "[%s] 本次批量处理完成：成功插入%s条，跳过%s条（含空值/已存在/异常）",
            self.config.domain_id,
            insert_count,
            skip_count,
        )

    def _insert_forensic_task_if_needed(self, forensic_data: dict[str, Any]) -> bool:
        task_id = forensic_data.get("taskId", "")

        with MySQLConnector(self.config.database) as db:
            query_result = db.execute_query(
                "SELECT COUNT(*) AS count FROM tasktest WHERE taskid = %s AND domain = %s",
                (task_id, self.config.domain_id),
            )
            task_count = query_result[0].get("count", 0) if query_result else 0
            if task_count >= 1:
                logger.info("任务[%s]：taskid已存在（count=%s），取消入库操作", task_id, task_count)
                return False

            platform = forensic_data.get("platform", "")
            appname = PLATFORM_MAP.get(platform, platform)
            room_id = forensic_data.get("roomId", "")
            url = forensic_data.get("url", "")
            if appname == "Xiuse":
                room_id = _extract_xiuse_room_id(room_id, url, task_id)

            db.execute_update(
                """
                INSERT INTO tasktest
                    (appname, task_args, title, roomid, casenum, taskid, forensic_type, domain)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    appname,
                    url,
                    forensic_data.get("title", ""),
                    room_id,
                    forensic_data.get("caseNum", ""),
                    task_id,
                    forensic_data.get("forensicType", ""),
                    self.config.domain_id,
                ),
            )

        return True


class ScheduledEvidenceThread(threading.Thread):
    def __init__(self, task_func: Callable[[], None], interval: int = 300, name: str | None = None):
        super().__init__(name=name or "EvidenceScheduledThread")
        self.task_func = task_func
        self.interval = interval
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()
        logger.info("线程 %s 已收到停止信号，将在当前周期结束后退出", self.name)

    def run(self) -> None:
        logger.info("定时线程[%s]已启动，将每%s秒执行一次", self.name, self.interval)
        while not self._stop_event.is_set():
            try:
                self.task_func()
            except Exception:
                logger.exception("定时线程[%s]执行任务时发生未捕获异常", self.name)

            for _ in range(self.interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)
