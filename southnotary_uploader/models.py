"""Domain models for forensic tasks and API payloads."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ForensicTaskRecord:
    """Row shape returned from MySQL tasktest."""

    id: int
    taskid: str
    videopath: str | None = None
    casenum: str | None = None
    start_time: dt.datetime | str | None = None
    end_time: dt.datetime | str | None = None
    appname: str | None = None
    domain: str | None = None
    complete: int | None = None
    upload: int | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ForensicTaskRecord":
        return cls(
            id=int(row.get("id", 0)),
            taskid=str(row.get("taskid", "")),
            videopath=row.get("videopath"),
            casenum=row.get("casenum"),
            start_time=row.get("start_time"),
            end_time=row.get("end_time"),
            appname=row.get("appname"),
            domain=row.get("domain"),
            complete=row.get("complete"),
            upload=row.get("upload"),
        )


@dataclass(frozen=True)
class ForensicApiTask:
    """Task item from getAutomatedForensics API."""

    task_id: str
    anchor_id: str = ""
    case_num: str = ""
    forensic_type: str = ""
    platform: str = ""
    room_id: str = ""
    title: str = ""
    url: str = ""

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "ForensicApiTask":
        return cls(
            task_id=str(payload.get("taskId", "")),
            anchor_id=str(payload.get("anchorId", "")),
            case_num=str(payload.get("caseNum", "")),
            forensic_type=str(payload.get("forensicType", "")),
            platform=str(payload.get("platform", "")),
            room_id=str(payload.get("roomId", "")),
            title=str(payload.get("title", "")),
            url=str(payload.get("url", "")),
        )


@dataclass(frozen=True)
class UploadCallbackPayload:
    obs_path: str
    case_num: str
    task_id: str
    screen_start_time: str
    screen_end_time: str
    file_hash: str

    def as_dict(self) -> dict[str, str]:
        return {
            "obsPath": self.obs_path,
            "caseNum": self.case_num,
            "taskId": self.task_id,
            "screenStartTime": self.screen_start_time,
            "screenEndTime": self.screen_end_time,
            "hash": self.file_hash,
        }
