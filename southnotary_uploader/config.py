from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


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


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer") from exc


@dataclass(frozen=True)
class ApiCredentials:
    appid: str
    randkey: str
    hashval: str


@dataclass(frozen=True)
class StorageConfig:
    access_key: str
    secret_key: str
    endpoint: str
    bucket: str
    signature_version: str = "s3"
    service_name: str = "s3"
    api_version: str = "2006-03-01"


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str = "utf8mb4"


@dataclass(frozen=True)
class AppConfig:
    domain_id: str
    base_url: str
    api_host: str
    credentials: ApiCredentials
    storage: StorageConfig
    database: DatabaseConfig
    evidence_fetch_interval_seconds: int
    upload_interval_seconds: int
    http_timeout_seconds: int
    log_level: str
    log_dir: Path

    @classmethod
    def from_env(cls) -> "AppConfig":
        default_log_dir = Path(__file__).resolve().parent.parent / "logs"

        return cls(
            domain_id=os.getenv("SOUTHNOTARY_DOMAIN_ID", "southnotary"),
            base_url=os.getenv("SOUTHNOTARY_BASE_URL", "https://www.southnotary.cn/api").rstrip("/"),
            api_host=os.getenv("SOUTHNOTARY_API_HOST", "www.southnotary.cn"),
            credentials=ApiCredentials(
                appid=_get_required_env("SOUTHNOTARY_APPID"),
                randkey=_get_required_env("SOUTHNOTARY_RANDKEY"),
                hashval=_get_required_env("SOUTHNOTARY_HASHVAL"),
            ),
            storage=StorageConfig(
                access_key=_get_required_env("OOS_ACCESS_KEY"),
                secret_key=_get_required_env("OOS_SECRET_KEY"),
                endpoint=os.getenv("OOS_ENDPOINT", "https://huanan2.zos.ctyun.cn"),
                bucket=os.getenv("OOS_BUCKET", "bucket-azy-southnotary"),
                signature_version=os.getenv("OOS_SIGNATURE_VERSION", "s3"),
                service_name=os.getenv("OOS_SERVICE_NAME", "s3"),
                api_version=os.getenv("OOS_API_VERSION", "2006-03-01"),
            ),
            database=DatabaseConfig(
                host=_get_required_env("MYSQL_HOST"),
                port=_get_int_env("MYSQL_PORT", 3306),
                user=_get_required_env("MYSQL_USER"),
                password=_get_required_env("MYSQL_PASSWORD"),
                database=_get_required_env("MYSQL_DATABASE"),
                charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
            ),
            evidence_fetch_interval_seconds=_get_int_env("EVIDENCE_FETCH_INTERVAL_SECONDS", 10),
            upload_interval_seconds=_get_int_env("UPLOAD_INTERVAL_SECONDS", 10),
            http_timeout_seconds=_get_int_env("HTTP_TIMEOUT_SECONDS", 30),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            log_dir=Path(os.getenv("LOG_DIR", str(default_log_dir))),
        )
