import logging
import re

from src.config import DOMAIN_ID, EVIDENCE_APPID, EVIDENCE_HASHVAL, EVIDENCE_RANDKEY, PLATFORM_MAP
from src.db_utils import MySQLConnector
from src.evidence_api import EvidenceApiClient

logger = logging.getLogger(__name__)


def evidence_api_worker() -> None:
    try:
        evidence_client = EvidenceApiClient()
        evidence_client.get_token(
            appid=EVIDENCE_APPID,
            randkey=EVIDENCE_RANDKEY,
            hashval=EVIDENCE_HASHVAL,
        )

        response = evidence_client.get_automated_forensics()
        evidence_client.pretty_print(response)

        if (
            response.get("code") != 200
            or not isinstance(response.get("data"), list)
            or not response.get("data")
        ):
            return

        forensic_data_list = response["data"]
        insert_count = 0
        skip_count = 0

        for forensic_data in forensic_data_list:
            task_id = forensic_data.get("taskId", "")

            if not task_id:
                skip_count += 1
                logger.warning("taskId为空，跳过数据入库")
                continue

            try:
                with MySQLConnector() as db:
                    query_result = db.execute_query(
                        "SELECT COUNT(*) AS count FROM tasktest WHERE taskid = %s AND domain = %s",
                        (task_id, DOMAIN_ID),
                    )
                    task_count = query_result[0].get("count", 0) if query_result else 0

                    if task_count >= 1:
                        skip_count += 1
                        logger.info(
                            "任务[%s]：taskid已存在（count=%s），取消入库操作",
                            task_id,
                            task_count,
                        )
                        continue

                    case_num = forensic_data.get("caseNum", "")
                    forensic_type = forensic_data.get("forensicType", "")
                    platform = forensic_data.get("platform", "")
                    appname = PLATFORM_MAP.get(platform, platform)
                    room_id = forensic_data.get("roomId", "")
                    title = forensic_data.get("title", "")
                    url = forensic_data.get("url", "")

                    if appname == "Xiuse" and str(room_id) == "0":
                        match = re.search(r"\d+$", url)
                        if match:
                            room_id = match.group(0)
                            logger.info(
                                "任务[%s]：Xiuse平台roomId为0，从URL提取新roomId: %s",
                                task_id,
                                room_id,
                            )

                    db.execute_update(
                        """INSERT INTO tasktest
                        (appname, task_args, title, roomid, casenum, taskid, forensic_type, domain)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            appname,
                            url,
                            title,
                            room_id,
                            case_num,
                            task_id,
                            forensic_type,
                            DOMAIN_ID,
                        ),
                    )

                insert_count += 1
                logger.info(
                    "任务[%s]：取证数据插入成功！taskId=%s, url=%s", task_id, task_id, url
                )

            except Exception as exc:
                skip_count += 1
                logger.error(
                    "任务[%s]：处理失败（查询/插入异常）: %s", task_id, exc, exc_info=True
                )

        logger.info(
            "[%s] 本次批量处理完成：成功插入%s条，跳过%s条（含空值/已存在/异常）",
            DOMAIN_ID,
            insert_count,
            skip_count,
        )

    except Exception as exc:
        logger.error(
            "[%s] 取证数据获取+入库任务执行失败: %s", DOMAIN_ID, exc, exc_info=True
        )
