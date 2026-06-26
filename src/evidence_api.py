import json
import logging
import traceback
from typing import Optional

import requests

from src.config import BASE_URL

logger = logging.getLogger(__name__)


class EvidenceApiClient:
    """Evidence API client for www.southnotary.cn."""

    def __init__(self, base_url: str = BASE_URL) -> None:
        self.base_url = base_url
        self.token = None
        self.expire_at = None

    def get_token(self, appid: str, randkey: str, hashval: str) -> dict:
        url = f"{self.base_url}/fh-evidence/openApi/v1/getCommAuthors"
        params = {"appid": appid, "randkey": randkey, "hashval": hashval}

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()

            if result.get("code") == "200":
                self.token = result.get("token")
                self.expire_at = result.get("expireAt")
                return result

            message = result.get("message", "unknown error")
            logger.error("Failed to get token: %s", message)
            raise RuntimeError(f"Failed to get token: {message}")

        except requests.exceptions.RequestException as exc:
            logger.error("HTTP Request error: %s", exc)
            raise
        except Exception as exc:
            logger.error("Error getting token: %s", exc)
            traceback.print_exc()
            raise

    def get_automated_forensics(self, token: Optional[str] = None) -> dict:
        current_token = token or self.token
        if not current_token:
            raise RuntimeError("No token available, please call get_token first")

        url = f"{self.base_url}/fh-evidence/openApi/v1/getAutomatedForensics?type=1"
        headers = {"gdazh-Access-Authorization": current_token}

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            logger.error("HTTP Request error: %s", exc)
            raise
        except Exception as exc:
            logger.error("Error getting automated forensics: %s", exc)
            traceback.print_exc()
            raise

    def pretty_print(self, response: dict) -> None:
        if response.get("code") != 200:
            logger.warning("=== API 返回非 200 错误 ===")
            logger.info(
                json.dumps(
                    response, sort_keys=True, indent=4, default=str, ensure_ascii=False
                )
            )
            return

        data = response.get("data", [])
        if data:
            logger.info(
                json.dumps(
                    response, sort_keys=True, indent=4, default=str, ensure_ascii=False
                )
            )
