from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Type

from db_utils import MySQLConnector

from .config import ScrcpyManagerConfig
from .platform_tasks import build_task_map


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoadedTask:
    task_id: int
    task_class: Type[Any]
    task_args: tuple[Any, ...]
    duration: int
    name: str


def _build_task_args(row: dict[str, Any], app_name: str, target_apps: set[str]) -> tuple[Any, ...]:
    if app_name in target_apps:
        room_id = row.get("roomid", "")
        return (room_id,) if room_id else ()
    raw_args = row.get("task_args", "")
    return (raw_args,) if raw_args else ()


def fetch_tasks_from_db(config: ScrcpyManagerConfig) -> list[LoadedTask]:
    task_map = build_task_map(config)
    tasks: list[LoadedTask] = []

    with MySQLConnector(config.database) as db:
        rows = db.execute_query(
            """
            SELECT *
            FROM tasktest
            WHERE complete = 0
              AND upload = 0
              AND domain = %s
            ORDER BY id ASC
            """,
            (config.system.domain_id,),
        )

    logger.info("从数据库加载了 %s 个待录制任务 (domain=%s)", len(rows), config.system.domain_id)

    for row in rows:
        app_name = row.get("appname")
        task_class = task_map.get(app_name)
        if not task_class:
            logger.warning("未知或未加载任务类型: %s，跳过 id=%s", app_name, row.get("id"))
            continue

        task_id = int(row.get("id", 0))
        duration = int(row.get("record_duration") or config.recording.duration)
        tasks.append(
            LoadedTask(
                task_id=task_id,
                task_class=task_class,
                task_args=_build_task_args(row, app_name, config.target_apps),
                duration=duration,
                name=f"{app_name}-{task_id}",
            )
        )

    return tasks
