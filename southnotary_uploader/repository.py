"""MySQL repository for tasktest operations."""

from __future__ import annotations

import logging
from typing import Any

from .config import DatabaseConfig
from .constants import PLATFORM_MAP
from .db_utils import MySQLConnector
from .models import ForensicApiTask, ForensicTaskRecord
from .utils import extract_xiuse_room_id


logger = logging.getLogger(__name__)


class TaskRepository:
    def __init__(self, database: DatabaseConfig, domain_id: str):
        self.database = database
        self.domain_id = domain_id

    def count_tasks_by_task_id(self, task_id: str) -> int:
        with MySQLConnector(self.database) as db:
            rows = db.execute_query(
                "SELECT COUNT(*) AS count FROM tasktest WHERE taskid = %s AND domain = %s",
                (task_id, self.domain_id),
            )
        return int(rows[0].get("count", 0)) if rows else 0

    def list_completed_pending_upload(self) -> list[ForensicTaskRecord]:
        with MySQLConnector(self.database) as db:
            rows = db.execute_query(
                """
                SELECT *
                FROM tasktest
                WHERE complete = 1 AND upload = 0 AND domain = %s
                ORDER BY id ASC
                """,
                (self.domain_id,),
            )
        return [ForensicTaskRecord.from_row(row) for row in rows]

    def insert_forensic_task(self, task: ForensicApiTask) -> None:
        appname = PLATFORM_MAP.get(task.platform, task.platform)
        room_id: Any = task.room_id
        if appname == "Xiuse":
            room_id = extract_xiuse_room_id(room_id, task.url, task.task_id)

        with MySQLConnector(self.database) as db:
            db.execute_update(
                """
                INSERT INTO tasktest
                    (appname, task_args, title, roomid, casenum, taskid, forensic_type, domain)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    appname,
                    task.url,
                    task.title,
                    room_id,
                    task.case_num,
                    task.task_id,
                    task.forensic_type,
                    self.domain_id,
                ),
            )

    def mark_uploaded(self, task_db_id: int) -> None:
        with MySQLConnector(self.database) as db:
            db.execute_update("UPDATE tasktest SET upload = 1 WHERE id = %s", (task_db_id,))

    def count_pending_upload(self) -> int:
        with MySQLConnector(self.database) as db:
            rows = db.execute_query(
                """
                SELECT COUNT(*) AS count
                FROM tasktest
                WHERE domain = %s AND complete = 1 AND upload = 0
                """,
                (self.domain_id,),
            )
        return int(rows[0].get("count", 0)) if rows else 0
