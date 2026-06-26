from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable, TypeVar

import requests
import urllib3

from .config import ApiCredentials
from .models import UploadCallbackPayload
from .utils import is_success_code


logger = logging.getLogger(__name__)
T = TypeVar("T")


def _disable_insecure_request_warnings(verify_ssl: bool) -> None:
    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class EvidenceApiClient:
    """Client for the Southnotary evidence open API."""

    def __init__(
        self,
        base_url: str,
        credentials: ApiCredentials,
        timeout_seconds: int = 30,
        retry_count: int = 3,
        retry_backoff_seconds: float = 1.0,
        verify_ssl: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.credentials = credentials
        self.timeout_seconds = timeout_seconds
        self.retry_count = max(1, retry_count)
        self.retry_backoff_seconds = max(0.0, retry_backoff_seconds)
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.token: str | None = None
        self.expire_at: str | None = None
        _disable_insecure_request_warnings(verify_ssl)

    def _request_with_retry(self, action: Callable[[], T]) -> T:
        last_error: Exception | None = None
        for attempt in range(1, self.retry_count + 1):
            try:
                return action()
            except requests.RequestException as exc:
                last_error = exc
                if attempt >= self.retry_count:
                    break
                sleep_seconds = self.retry_backoff_seconds * attempt
                logger.warning(
                    "HTTP request failed (attempt %s/%s): %s; retrying in %.1fs",
                    attempt,
                    self.retry_count,
                    exc,
                    sleep_seconds,
                )
                time.sleep(sleep_seconds)
        assert last_error is not None
        raise last_error

    def get_token(self) -> dict[str, Any]:
        url = f"{self.base_url}/fh-evidence/openApi/v1/getCommAuthors"
        params = {
            "appid": self.credentials.appid,
            "randkey": self.credentials.randkey,
            "hashval": self.credentials.hashval,
        }

        def _do_request() -> dict[str, Any]:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout_seconds,
                verify=self.verify_ssl,
            )
            response.raise_for_status()
            return response.json()

        result = self._request_with_retry(_do_request)

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

        def _do_request() -> dict[str, Any]:
            response = self.session.get(
                url,
                params={"type": 1},
                headers=headers,
                timeout=self.timeout_seconds,
                verify=self.verify_ssl,
            )
            response.raise_for_status()
            return response.json()

        return self._request_with_retry(_do_request)

    def upload_automated_forensics_file(
        self,
        payload: UploadCallbackPayload,
        token: str | None = None,
    ) -> tuple[int, str, dict[str, Any] | None]:
        current_token = token or self.token
        if not current_token:
            raise RuntimeError("No token available, please call get_token first")

        headers = {
            "gdazh-Access-Authorization": current_token,
            "Content-Type": "application/json; charset=utf-8",
            "Connection": "close",
        }
        url = f"{self.base_url}/fh-evidence/openApi/v1/uploadAutomatedForensicsFile"
        body = json.dumps(payload.as_dict(), ensure_ascii=False).encode("utf-8")

        def _do_request() -> requests.Response:
            return self.session.post(
                url,
                data=body,
                headers=headers,
                timeout=self.timeout_seconds,
                verify=self.verify_ssl,
            )

        response = self._request_with_retry(_do_request)
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
