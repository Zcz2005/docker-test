from __future__ import annotations

import json
import logging
from typing import Any

import requests

from .config import ApiCredentials


logger = logging.getLogger(__name__)


def is_success_code(code: Any) -> bool:
    return str(code) == "200"


class EvidenceApiClient:
    """Client for the Southnotary evidence open API."""

    def __init__(self, base_url: str, credentials: ApiCredentials, timeout_seconds: int = 30):
        self.base_url = base_url.rstrip("/")
        self.credentials = credentials
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.token: str | None = None
        self.expire_at: str | None = None

    def get_token(self) -> dict[str, Any]:
        url = f"{self.base_url}/fh-evidence/openApi/v1/getCommAuthors"
        params = {
            "appid": self.credentials.appid,
            "randkey": self.credentials.randkey,
            "hashval": self.credentials.hashval,
        }

        response = self.session.get(url, params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        result = response.json()

        if not is_success_code(result.get("code")):
            raise RuntimeError(f"Failed to get token: {result.get('message')}")

        self.token = result.get("token")
        self.expire_at = result.get("expireAt")
        if not self.token:
            raise RuntimeError("Token response did not include token")

        return result

    def get_automated_forensics(self, token: str | None = None) -> dict[str, Any]:
        current_token = token or self.token
        if not current_token:
            raise RuntimeError("No token available, please call get_token first")

        url = f"{self.base_url}/fh-evidence/openApi/v1/getAutomatedForensics"
        headers = {"gdazh-Access-Authorization": current_token}
        response = self.session.get(
            url,
            params={"type": 1},
            headers=headers,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def upload_automated_forensics_file(
        self,
        obs_path: str,
        case_num: str,
        task_id: str,
        screen_start_time: str,
        screen_end_time: str,
        file_hash: str,
        token: str | None = None,
    ) -> tuple[int, str, dict[str, Any] | None]:
        current_token = token or self.token
        if not current_token:
            raise RuntimeError("No token available, please call get_token first")

        payload = {
            "obsPath": obs_path,
            "caseNum": case_num,
            "taskId": task_id,
            "screenStartTime": screen_start_time,
            "screenEndTime": screen_end_time,
            "hash": file_hash,
        }
        headers = {
            "gdazh-Access-Authorization": current_token,
            "Content-Type": "application/json; charset=utf-8",
            "Connection": "close",
        }
        url = f"{self.base_url}/fh-evidence/openApi/v1/uploadAutomatedForensicsFile"

        response = self.session.post(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            timeout=self.timeout_seconds,
        )
        response_text = response.text

        try:
            response_json = response.json()
        except ValueError:
            response_json = None

        return response.status_code, response_text, response_json

    @staticmethod
    def pretty_print(response: dict[str, Any]) -> None:
        if not is_success_code(response.get("code")):
            print("=== API 返回非 200 错误 ===")
            print(json.dumps(response, sort_keys=True, indent=4, default=str, ensure_ascii=False))
            return

        data = response.get("data", [])
        if data:
            print(json.dumps(response, sort_keys=True, indent=4, default=str, ensure_ascii=False))
