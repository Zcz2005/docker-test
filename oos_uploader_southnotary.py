#!/usr/bin/env python3
"""
南方公证处取证任务同步 + 天翼云 OOS/ZOS 视频上传服务（单文件版）

由原始 oos_uploader_southnotary 脚本重新生成：
- 保留全部业务逻辑与双线程调度模型
- 凭证、数据库连接改为环境变量 / .env 配置（不硬编码密钥）
- 兼容 from db_utils import MySQLConnector

运行：
    cp .env.example .env   # 填入真实配置
    python oos_uploader_southnotary.py
"""

from __future__ import annotations

import datetime
import hashlib
import http.client
import json
import logging
import os
import re
import sys
import threading
import time
import traceback
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------------------------
# 环境变量 / .env
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# ZOS endpoint 补丁（与原脚本一致）
# ---------------------------------------------------------------------------
import ooscore.args

ooscore.args.REGION_PATTERN = r".*(oos|zos)-(?P<region>[a-zA-Z0-9\-]+?)(-sts)?\."
ooscore.args.REGION_RE = re.compile(ooscore.args.REGION_PATTERN)


def _patched_get_ctyun_region_re(self, endpoint_url):
    from ooscore.compat import urlsplit

    hostname = urlsplit(endpoint_url).hostname
    match = ooscore.args.REGION_RE.match(hostname or "")
    if match and match.group("region"):
        return match.group("region"), match.group("region")
    if hostname and ".zos." in hostname:
        parts = hostname.split(".")
        if len(parts) >= 3 and parts[1] == "zos":
            return parts[0], parts[0]
    raise Exception("Invalid Endpoint!")


ooscore.args.ClientArgsCreator._get_ctyun_region_re = _patched_get_ctyun_region_re

import oos
import ooscore.exceptions as exceptions
from ooscore.client import Config

from db_utils import MySQLConnector

# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
LOG_DIR = os.getenv("LOG_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"))
os.makedirs(LOG_DIR, exist_ok=True)

log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
root_logger = logging.getLogger()
root_logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

file_handler = TimedRotatingFileHandler(
    filename=os.path.join(LOG_DIR, "oos_uploader_southnotary.log"),
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8",
)
file_handler.suffix = "%Y-%m-%d.log"
file_handler.setFormatter(log_formatter)
root_logger.addHandler(file_handler)

# ---------------------------------------------------------------------------
# 业务常量
# ---------------------------------------------------------------------------
PLATFORM_MAP = {
    "3": "Douyin",
    "5": "Kuaishou",
    "7": "Ailiao",
    "11": "Huajiao",
    "12": "Yingke",
    "14": "Lespark",
    "17": "Mifeng",
    "18": "Momo",
    "21": "Xiaohongshu",
    "22": "Xiuse",
    "24": "Baobao",
    "27": "Kelakela",
    "33": "Aichang",
    "36": "Lingsheng",
    "43": "Hongguo",
}

CURRENT_DOMAIN_ID = os.getenv("SOUTHNOTARY_DOMAIN_ID", "southnotary")
CURRENT_BASE_URL = os.getenv("SOUTHNOTARY_BASE_URL", "https://www.southnotary.cn/api").rstrip("/")
CURRENT_API_HOST = os.getenv("SOUTHNOTARY_API_HOST", "www.southnotary.cn")

SOUTHNOTARY_APPID = os.environ["SOUTHNOTARY_APPID"]
SOUTHNOTARY_RANDKEY = os.environ["SOUTHNOTARY_RANDKEY"]
SOUTHNOTARY_HASHVAL = os.environ["SOUTHNOTARY_HASHVAL"]

OOS_ACCESS_KEY = os.environ["OOS_ACCESS_KEY"]
OOS_SECRET_KEY = os.environ["OOS_SECRET_KEY"]
OOS_ENDPOINT = os.getenv("OOS_ENDPOINT", "https://huanan2.zos.ctyun.cn")
OOS_BUCKET = os.getenv("OOS_BUCKET", "bucket-azy-southnotary")

EVIDENCE_FETCH_INTERVAL = int(os.getenv("EVIDENCE_FETCH_INTERVAL_SECONDS", "10"))
UPLOAD_INTERVAL = int(os.getenv("UPLOAD_INTERVAL_SECONDS", "10"))
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT_SECONDS", "30"))


def _success_code(code) -> bool:
    return str(code) == "200"


class OOSUploader:
    """OOS Single File Upload Class"""

    def __init__(
        self,
        access_key,
        secret_key,
        endpoint,
        bucket,
        signature_version="s3",
        service_name="s3",
        api_version="2006-03-01",
    ):
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint = endpoint
        self.bucket = bucket
        self.signature_version = signature_version
        self.service_name = service_name
        self.api_version = api_version
        self.client = self._init_client()

    def _init_client(self):
        endpoint = self.endpoint
        if endpoint.lower().find("http") < 0 and endpoint.lower().find("https") < 0:
            endpoint = "http://" + endpoint

        try:
            _config = Config(
                endpoint_url=endpoint,
                signature_version=self.signature_version,
                s3={"payload_signing_enabled": True},
            )
            client = oos.client(
                service_name=self.service_name,
                endpoint_url=endpoint,
                api_version=self.api_version,
                access_key_id=self.access_key,
                secret_access_key=self.secret_key,
                config=_config,
            )
            return client
        except Exception as ex:
            logging.error(traceback.format_exc())
            logging.error("Client initialization error: %s", ex)
            raise

    @staticmethod
    def pretty_print(res):
        print(json.dumps(res, sort_keys=True, indent=4, default=str, ensure_ascii=False))

    def upload_file(
        self,
        local_file_path,
        object_key,
        storage_class="STANDARD",
        content_type="application/octet-stream",
        data_location=None,
        forbid_overwrite=False,
    ):
        try:
            params = {
                "Bucket": self.bucket,
                "Key": object_key,
                "StorageClass": storage_class,
                "ContentType": content_type,
                "ForbidOverWrite": forbid_overwrite,
            }
            if data_location:
                params["DataLocation"] = data_location

            with open(local_file_path, "rb") as data:
                params["Body"] = data
                response = self.client.put_object(**params)

            print(f"File uploaded successfully: {local_file_path} -> {object_key}")
            return response

        except exceptions.ClientError as e:
            error_msg = (
                f"\n Response code: {e.response['Error']['Code']}\n"
                f" Error message: {e.response['Error']['Message']}\n"
                f" Resource: {e.response['Error']['Resource']}\n"
                f" request id: {e.response['ResponseMetadata']['RequestId']}"
            )
            print(error_msg)
            raise
        except Exception as ex:
            print(f"Upload error: {ex}")
            traceback.print_exc()
            raise


def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logging.error("计算文件哈希值失败: %s", e)
        traceback.print_exc()
        raise


class EvidenceApiClient:
    """Evidence API Client Class - www.southnotary.cn"""

    def __init__(self, base_url=CURRENT_BASE_URL):
        self.base_url = base_url
        self.token = None
        self.expire_at = None

    def get_token(self, appid, randkey, hashval):
        url = f"{self.base_url}/fh-evidence/openApi/v1/getCommAuthors"
        params = {"appid": appid, "randkey": randkey, "hashval": hashval}
        try:
            response = requests.get(url, params=params, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            result = response.json()
            if _success_code(result.get("code")):
                self.token = result.get("token")
                self.expire_at = result.get("expireAt")
                return result
            print(f"Failed to get token: {result.get('message')}")
            raise Exception(f"Failed to get token: {result.get('message')}")
        except requests.exceptions.RequestException as e:
            print(f"HTTP Request error: {e}")
            raise

    def get_automated_forensics(self, token=None):
        current_token = token or self.token
        if not current_token:
            raise Exception("No token available, please call get_token first")

        url = f"{self.base_url}/fh-evidence/openApi/v1/getAutomatedForensics?type=1"
        headers = {"gdazh-Access-Authorization": current_token}
        try:
            response = requests.request("GET", url, headers=headers, data={}, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"HTTP Request error: {e}")
            raise

    def pretty_print(self, res):
        if not _success_code(res.get("code")):
            print("=== API 返回非 200 错误 ===")
            print(json.dumps(res, sort_keys=True, indent=4, default=str, ensure_ascii=False))
            return
        data = res.get("data", [])
        if data:
            print(json.dumps(res, sort_keys=True, indent=4, default=str, ensure_ascii=False))


def upload_completed_tasks():
    try:
        evidence_client = EvidenceApiClient()
        evidence_client.get_token(
            appid=SOUTHNOTARY_APPID,
            randkey=SOUTHNOTARY_RANDKEY,
            hashval=SOUTHNOTARY_HASHVAL,
        )

        if not evidence_client.token:
            print("警告：evidence_client未提供或未获取token，将无法调用回调接口")

        uploader = OOSUploader(
            access_key=OOS_ACCESS_KEY,
            secret_key=OOS_SECRET_KEY,
            endpoint=OOS_ENDPOINT,
            bucket=OOS_BUCKET,
        )

        with MySQLConnector() as db:
            completed_tasks = db.execute_query(
                "SELECT * FROM tasktest WHERE complete = 1 AND upload = 0 AND domain = %s",
                (CURRENT_DOMAIN_ID,),
            )

        logging.info("共查询到 %s 个已完成的任务", len(completed_tasks))

        for task in completed_tasks:
            task_id = task.get("taskid", "")
            try:
                row_id = task.get("id", "")
                video_path = task.get("videopath", "")

                if not video_path:
                    logging.warning("任务[%s]：videopath为空，跳过上传", task_id)
                    continue

                if not os.path.exists(video_path):
                    logging.error("任务[%s]：文件不存在，跳过上传: %s", task_id, video_path)
                    continue

                logging.info("任务[%s]：开始计算文件哈希值: %s", task_id, video_path)
                file_hash = calculate_sha256(video_path)
                logging.info("任务[%s]：文件哈希值计算完成: %s", task_id, file_hash)

                today = datetime.datetime.now().strftime("%Y-%m-%d")
                timestamp = int(datetime.datetime.now().timestamp())
                object_key = f"evidenceProd/Casefile/File/{today}/{timestamp}/{os.path.basename(video_path)}"

                logging.info("任务[%s]：开始上传文件到OOS: %s -> %s", task_id, video_path, object_key)
                try:
                    response = uploader.upload_file(
                        local_file_path=video_path,
                        object_key=object_key,
                        storage_class="STANDARD",
                        content_type="video/mp4",
                    )
                    if not (response and isinstance(response, dict)):
                        logging.error("任务[%s]：文件上传响应异常，未更新数据库", task_id)
                        continue
                    logging.info("任务[%s]：文件上传成功！taskId=%s, objectKey=%s", task_id, task_id, object_key)
                except Exception as upload_e:
                    logging.error("任务[%s]：文件上传失败: %s", task_id, upload_e)
                    traceback.print_exc()
                    continue

                if not (task_id and evidence_client.token):
                    continue

                start_time = task.get("start_time", "")
                if isinstance(start_time, datetime.datetime):
                    start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")

                end_time = task.get("end_time", "")
                if isinstance(end_time, datetime.datetime):
                    end_time = end_time.strftime("%Y-%m-%d %H:%M:%S")

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

                conn = http.client.HTTPSConnection(CURRENT_API_HOST, 443, timeout=HTTP_TIMEOUT)
                conn.request("POST", "/api/fh-evidence/openApi/v1/uploadAutomatedForensicsFile", payload, headers)
                res = conn.getresponse()
                response_str = res.read().decode("utf-8")
                conn.close()

                print("\n" + "=" * 50)
                print(f"响应内容：\n{response_str}")
                print("=" * 50 + "\n")

                if res.status != 200:
                    logging.error("任务[%s]：接口返回非200状态码！状态码：%s，响应：%s", task_id, res.status, response_str)
                    continue

                try:
                    response_json = json.loads(response_str)
                except json.JSONDecodeError:
                    logging.error("任务[%s]：接口响应非JSON格式，无法解析！响应：%s", task_id, response_str)
                    continue

                business_code = response_json.get("code", -1)
                message = response_json.get("message", "")

                if str(business_code) == "500" and message in ("取证任务已结束！", "取证任务不存在！"):
                    logging.info("任务[%s]：%s，直接更新数据库", task_id, message)
                    with MySQLConnector() as db:
                        db.execute_update("UPDATE tasktest SET upload = 1 WHERE id = %s", (row_id,))
                    logging.info("任务[%s]：数据库更新成功，id=%s的upload字段已设为1", task_id, row_id)
                    continue

                if not _success_code(business_code):
                    err_msg = response_json.get("message", "无错误信息")
                    logging.error(
                        "任务[%s]：接口业务处理失败！业务code：%s，错误信息：%s，响应：%s",
                        task_id,
                        business_code,
                        err_msg,
                        response_str,
                    )
                    continue

                with MySQLConnector() as db:
                    db.execute_update("UPDATE tasktest SET upload = 1 WHERE id = %s", (row_id,))
                logging.info("任务[%s]：数据库更新成功，id=%s的upload字段已设为1", task_id, row_id)

            except Exception as e:
                logging.error("任务[%s]：任务处理失败: %s", task_id, e)
                traceback.print_exc()
                continue

        print(f"=== [{CURRENT_DOMAIN_ID}] 所有已完成任务的视频文件上传完成 ===")

    except Exception as e:
        logging.error("OOS文件上传任务执行失败: %s", e, exc_info=True)


def evidence_api_worker():
    try:
        evidence_client = EvidenceApiClient()
        evidence_client.get_token(
            appid=SOUTHNOTARY_APPID,
            randkey=SOUTHNOTARY_RANDKEY,
            hashval=SOUTHNOTARY_HASHVAL,
        )

        response = evidence_client.get_automated_forensics()
        evidence_client.pretty_print(response)

        if not (_success_code(response.get("code")) and isinstance(response.get("data"), list)):
            return

        forensic_data_list = response.get("data", [])
        if not forensic_data_list:
            return

        insert_count = 0
        skip_count = 0

        for forensic_data in forensic_data_list:
            task_id = forensic_data.get("taskId", "")
            if not task_id:
                skip_count += 1
                logging.warning("taskId为空，跳过数据入库")
                continue

            try:
                with MySQLConnector() as db:
                    query_result = db.execute_query(
                        "SELECT COUNT(*) AS count FROM tasktest WHERE taskid = %s AND domain = %s",
                        (task_id, CURRENT_DOMAIN_ID),
                    )
                    task_count = query_result[0].get("count", 0) if query_result else 0
                    if task_count >= 1:
                        skip_count += 1
                        logging.info("任务[%s]：taskid已存在（count=%s），取消入库操作", task_id, task_count)
                        continue

                    platform = forensic_data.get("platform", "")
                    appname = PLATFORM_MAP.get(platform, platform)
                    room_id = forensic_data.get("roomId", "")
                    url = forensic_data.get("url", "")

                    if appname == "Xiuse" and str(room_id) == "0":
                        match = re.search(r"\d+$", url or "")
                        if match:
                            room_id = match.group(0)
                            logging.info("任务[%s]：Xiuse平台roomId为0，从URL提取新roomId: %s", task_id, room_id)

                    db.execute_update(
                        """INSERT INTO tasktest
                        (appname, task_args, title, roomid, casenum, taskid, forensic_type, domain)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            appname,
                            url,
                            forensic_data.get("title", ""),
                            room_id,
                            forensic_data.get("caseNum", ""),
                            task_id,
                            forensic_data.get("forensicType", ""),
                            CURRENT_DOMAIN_ID,
                        ),
                    )

                insert_count += 1
                logging.info("任务[%s]：取证数据插入成功！taskId=%s, url=%s", task_id, task_id, url)

            except Exception as e:
                skip_count += 1
                logging.error("任务[%s]：处理失败（查询/插入异常）: %s", task_id, e, exc_info=True)

        logging.info(
            "[%s] 本次批量处理完成：成功插入%s条，跳过%s条（含空值/已存在/异常）",
            CURRENT_DOMAIN_ID,
            insert_count,
            skip_count,
        )

    except Exception as e:
        logging.error("[%s] 取证数据获取+入库任务执行失败: %s", CURRENT_DOMAIN_ID, e, exc_info=True)


class ScheduledEvidenceThread(threading.Thread):
    def __init__(self, task_func, interval: int = 300, name: Optional[str] = None):
        super().__init__(name=name or "EvidenceScheduledThread", daemon=True)
        self.task_func = task_func
        self.interval = interval
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()
        logging.info("线程 %s 已收到停止信号，将在当前周期结束后退出", self.name)

    def run(self):
        logging.info("[%s] 定时线程[%s]已启动，将每%s秒执行一次", CURRENT_DOMAIN_ID, self.name, self.interval)
        while not self._stop_event.is_set():
            try:
                self.task_func()
            except Exception as e:
                logging.error(
                    "[%s] 定时线程[%s]执行任务时发生未捕获异常: %s",
                    CURRENT_DOMAIN_ID,
                    self.name,
                    e,
                    exc_info=True,
                )
            for _ in range(self.interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)


def main():
    logging.info("=== 启动 [%s] 服务 ===", CURRENT_DOMAIN_ID)

    evidence_thread = ScheduledEvidenceThread(
        task_func=evidence_api_worker,
        interval=EVIDENCE_FETCH_INTERVAL,
        name="EvidenceDataThread",
    )
    upload_thread = ScheduledEvidenceThread(
        task_func=upload_completed_tasks,
        interval=UPLOAD_INTERVAL,
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
    try:
        main()
    except KeyError as exc:
        print(f"缺少必填环境变量: {exc}", file=sys.stderr)
        print("请复制 .env.example 为 .env 并填写配置", file=sys.stderr)
        raise SystemExit(1) from exc
