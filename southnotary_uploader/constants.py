"""Shared constants for the Southnotary uploader service."""

from __future__ import annotations

PLATFORM_MAP: dict[str, str] = {
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

DEFAULT_DOMAIN_ID = "southnotary"
DEFAULT_BASE_URL = "https://www.southnotary.cn/api"
DEFAULT_API_HOST = "www.southnotary.cn"
DEFAULT_OOS_ENDPOINT = "https://huanan2.zos.ctyun.cn"
DEFAULT_OOS_BUCKET = "bucket-azy-southnotary"
DEFAULT_OBJECT_KEY_PREFIX = "evidenceProd/Casefile/File"

TERMINAL_UPLOAD_MESSAGES = frozenset(
    {
        "取证任务已结束！",
        "取证任务不存在！",
    }
)

SUCCESS_API_CODE = "200"
TERMINAL_BUSINESS_CODE = "500"

DEFAULT_EVIDENCE_FETCH_INTERVAL_SECONDS = 10
DEFAULT_UPLOAD_INTERVAL_SECONDS = 10
DEFAULT_HTTP_TIMEOUT_SECONDS = 30
DEFAULT_API_RETRY_COUNT = 3
DEFAULT_API_RETRY_BACKOFF_SECONDS = 1.0
