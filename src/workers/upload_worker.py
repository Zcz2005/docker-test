import datetime
import http.client
import json
import logging
import os
import traceback

from src.config import (
    API_HOST,
    DOMAIN_ID,
    EVIDENCE_APPID,
    EVIDENCE_HASHVAL,
    EVIDENCE_RANDKEY,
    OOS_ACCESS_KEY,
    OOS_BUCKET,
    OOS_ENDPOINT,
    OOS_SECRET_KEY,
)
from src.db_utils import MySQLConnector
from src.evidence_api import EvidenceApiClient
from src.oos_client import OOSUploader
from src.utils.hash_utils import calculate_sha256

logger = logging.getLogger(__name__)


def _mark_task_uploaded(task_db_id) -> None:
    with MySQLConnector() as db:
        db.execute_update(
            "UPDATE tasktest SET upload = 1 WHERE id = %s",
            (task_db_id,),
        )
    logger.info("数据库更新成功，id=%s 的 upload 字段已设为 1", task_db_id)


def _notify_upload_callback(
    evidence_client: EvidenceApiClient,
    task: dict,
    task_id: str,
    object_key: str,
    file_hash: str,
):
    start_time = task.get("start_time", "")
    if isinstance(start_time, datetime.datetime):
        start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")

    end_time = task.get("end_time", "")
    if isinstance(end_time, datetime.datetime):
        end_time = end_time.strftime("%Y-%m-%d %H:%M:%S")

    conn = http.client.HTTPSConnection(API_HOST, 443, timeout=30)
    payload = json.dumps(
        {
            "obsPath": object_key,
            "caseNum": task.get("casenum", ""),
            "taskId": task_id,
            "screenStartTime": start_time,
            "screenEndTime": end_time,
            "hash": file_hash,
        },
        ensure_ascii=False,
    )
    headers = {
        "gdazh-Access-Authorization": evidence_client.token,
        "Content-Type": "application/json; charset=utf-8",
        "Connection": "close",
    }

    conn.request(
        "POST",
        "/api/fh-evidence/openApi/v1/uploadAutomatedForensicsFile",
        payload,
        headers,
    )
    res = conn.getresponse()
    response_str = res.read().decode("utf-8")

    logger.info("任务[%s] 回调响应：%s", task_id, response_str)

    if res.status != 200:
        logger.error(
            "任务[%s]：接口返回非200状态码！状态码：%s，响应：%s",
            task_id,
            res.status,
            response_str,
        )
        return False, response_str

    try:
        response_json = json.loads(response_str)
    except json.JSONDecodeError:
        logger.error(
            "任务[%s]：接口响应非JSON格式，无法解析！响应：%s",
            task_id,
            response_str,
        )
        return False, response_str

    business_code = response_json.get("code", -1)
    message = response_json.get("message", "")

    if business_code == 500 and message in ("取证任务已结束！", "取证任务不存在！"):
        logger.info("任务[%s]：%s，直接更新数据库", task_id, message)
        return True, response_str

    if business_code != 200:
        err_msg = response_json.get("message", "无错误信息")
        logger.error(
            "任务[%s]：接口业务处理失败！业务code：%s，错误信息：%s，响应：%s",
            task_id,
            business_code,
            err_msg,
            response_str,
        )
        return False, response_str

    return True, response_str


def upload_completed_tasks() -> None:
    try:
        evidence_client = EvidenceApiClient()
        evidence_client.get_token(
            appid=EVIDENCE_APPID,
            randkey=EVIDENCE_RANDKEY,
            hashval=EVIDENCE_HASHVAL,
        )

        if not evidence_client.token:
            logger.warning("未获取 token，将无法调用回调接口")

        uploader = OOSUploader(
            access_key=OOS_ACCESS_KEY,
            secret_key=OOS_SECRET_KEY,
            endpoint=OOS_ENDPOINT,
            bucket=OOS_BUCKET,
        )

        with MySQLConnector() as db:
            completed_tasks = db.execute_query(
                "SELECT * FROM tasktest WHERE complete = 1 AND upload = 0 AND domain = %s",
                (DOMAIN_ID,),
            )

        logger.info("共查询到 %s 个已完成的任务", len(completed_tasks))

        for task in completed_tasks:
            task_db_id = task.get("id", "")
            task_id = task.get("taskid", "")
            video_path = task.get("videopath", "")

            try:
                if not video_path:
                    logger.warning("任务[%s]：videopath为空，跳过上传", task_id)
                    continue

                if not os.path.exists(video_path):
                    logger.error(
                        "任务[%s]：文件不存在，跳过上传: %s", task_id, video_path
                    )
                    continue

                logger.info("任务[%s]：开始计算文件哈希值: %s", task_id, video_path)
                file_hash = calculate_sha256(video_path)
                logger.info("任务[%s]：文件哈希值计算完成: %s", task_id, file_hash)

                today = datetime.datetime.now().strftime("%Y-%m-%d")
                timestamp = int(datetime.datetime.now().timestamp())
                object_key = (
                    f"evidenceProd/Casefile/File/{today}/{timestamp}/"
                    f"{os.path.basename(video_path)}"
                )

                logger.info(
                    "任务[%s]：开始上传文件到OOS: %s -> %s",
                    task_id,
                    video_path,
                    object_key,
                )

                try:
                    response = uploader.upload_file(
                        local_file_path=video_path,
                        object_key=object_key,
                        storage_class="STANDARD",
                        content_type="video/mp4",
                    )
                except Exception as upload_exc:
                    logger.error(
                        "任务[%s]：文件上传失败: %s", task_id, upload_exc, exc_info=True
                    )
                    continue

                if not response or not isinstance(response, dict):
                    logger.error("任务[%s]：文件上传响应异常，未更新数据库", task_id)
                    continue

                logger.info(
                    "任务[%s]：文件上传成功！taskId=%s, objectKey=%s",
                    task_id,
                    task_id,
                    object_key,
                )

                if not task_id or not evidence_client.token:
                    continue

                try:
                    success, _ = _notify_upload_callback(
                        evidence_client, task, task_id, object_key, file_hash
                    )
                    if success:
                        _mark_task_uploaded(task_db_id)
                except Exception as callback_exc:
                    logger.error(
                        "任务[%s]：回调接口调用异常: %s",
                        task_id,
                        callback_exc,
                        exc_info=True,
                    )

            except Exception as exc:
                logger.error(
                    "任务[%s]：任务处理失败: %s", task_id, exc, exc_info=True
                )

        logger.info("=== [%s] 所有已完成任务的视频文件上传完成 ===", DOMAIN_ID)

    except Exception as exc:
        logger.error("上传已完成任务的视频文件失败: %s", exc, exc_info=True)
