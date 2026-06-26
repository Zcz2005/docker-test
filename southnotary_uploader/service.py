from __future__ import annotations

import logging
from pathlib import Path

from .api import EvidenceApiClient
from .config import AppConfig
from .constants import TERMINAL_BUSINESS_CODE, TERMINAL_UPLOAD_MESSAGES
from .models import ForensicApiTask, UploadCallbackPayload
from .object_key import build_object_key
from .repository import TaskRepository
from .storage import OOSUploader, calculate_sha256
from .utils import format_datetime, is_success_code


logger = logging.getLogger(__name__)


class EvidenceTaskService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.repository = TaskRepository(config.database, config.domain_id)

    def _new_api_client_with_token(self) -> EvidenceApiClient:
        evidence_client = EvidenceApiClient(
            base_url=self.config.base_url,
            credentials=self.config.credentials,
            timeout_seconds=self.config.http_timeout_seconds,
            retry_count=self.config.api_retry_count,
            retry_backoff_seconds=self.config.api_retry_backoff_seconds,
            verify_ssl=self.config.verify_ssl,
        )
        evidence_client.get_token()
        return evidence_client

    def upload_completed_tasks(self) -> None:
        evidence_client = self._new_api_client_with_token()
        uploader = OOSUploader(self.config.storage)
        completed_tasks = self.repository.list_completed_pending_upload()

        logger.info("共查询到 %s 个已完成的任务", len(completed_tasks))

        for task in completed_tasks:
            try:
                self._upload_one_completed_task(task, evidence_client, uploader)
            except Exception:
                logger.exception("任务[%s]：任务处理失败", task.taskid)

        print(f"=== [{self.config.domain_id}] 所有已完成任务的视频文件上传完成 ===")

    def _upload_one_completed_task(
        self,
        task,
        evidence_client: EvidenceApiClient,
        uploader: OOSUploader,
    ) -> None:
        task_id = task.taskid
        video_path = task.videopath

        if not video_path:
            logger.warning("任务[%s]：videopath为空，跳过上传", task_id)
            return

        if not Path(video_path).exists():
            logger.error("任务[%s]：文件不存在，跳过上传: %s", task_id, video_path)
            return

        logger.info("任务[%s]：开始计算文件哈希值: %s", task_id, video_path)
        file_hash = calculate_sha256(video_path)
        logger.info("任务[%s]：文件哈希值计算完成: %s", task_id, file_hash)

        object_key = build_object_key(video_path, prefix=self.config.storage.object_key_prefix)

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

        callback_payload = UploadCallbackPayload(
            obs_path=object_key,
            case_num=task.casenum or "",
            task_id=task_id,
            screen_start_time=format_datetime(task.start_time),
            screen_end_time=format_datetime(task.end_time),
            file_hash=file_hash,
        )
        status_code, response_text, response_json = evidence_client.upload_automated_forensics_file(
            callback_payload
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

        if str(business_code) == TERMINAL_BUSINESS_CODE and message in TERMINAL_UPLOAD_MESSAGES:
            logger.info("任务[%s]：%s，直接更新数据库", task_id, message)
            self._mark_task_uploaded(task.id, task_id)
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

        self._mark_task_uploaded(task.id, task_id)

    def _mark_task_uploaded(self, task_db_id: int, task_id: str) -> None:
        try:
            self.repository.mark_uploaded(task_db_id)
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
            task = ForensicApiTask.from_api(forensic_data)
            if not task.task_id:
                skip_count += 1
                logger.warning("taskId为空，跳过数据入库")
                continue

            try:
                if self.repository.count_tasks_by_task_id(task.task_id) >= 1:
                    skip_count += 1
                    logger.info("任务[%s]：taskid已存在，取消入库操作", task.task_id)
                    continue

                self.repository.insert_forensic_task(task)
                insert_count += 1
                logger.info(
                    "任务[%s]：取证数据插入成功！taskId=%s, url=%s",
                    task.task_id,
                    task.task_id,
                    task.url,
                )
            except Exception:
                skip_count += 1
                logger.exception("任务[%s]：处理失败（查询/插入异常）", task.task_id)

        logger.info(
            "[%s] 本次批量处理完成：成功插入%s条，跳过%s条（含空值/已存在/异常）",
            self.config.domain_id,
            insert_count,
            skip_count,
        )
