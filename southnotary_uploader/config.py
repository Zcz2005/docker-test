from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .constants import (
    DEFAULT_API_HOST,
    DEFAULT_BASE_URL,
    DEFAULT_DOMAIN_ID,
    DEFAULT_EVIDENCE_FETCH_INTERVAL_SECONDS,
    DEFAULT_HTTP_TIMEOUT_SECONDS,
    DEFAULT_OBJECT_KEY_PREFIX,
    DEFAULT_OOS_BUCKET,
    DEFAULT_OOS_ENDPOINT,
    DEFAULT_UPLOAD_INTERVAL_SECONDS,
    DEFAULT_API_RETRY_BACKOFF_SECONDS,
    DEFAULT_API_RETRY_COUNT,
)


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


def _get_float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be a number") from exc


def _get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


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
    object_key_prefix: str = DEFAULT_OBJECT_KEY_PREFIX
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
    connect_timeout_seconds: int = 10


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
    api_retry_count: int
    api_retry_backoff_seconds: float
    verify_ssl: bool
    log_level: str
    log_dir: Path

    @classmethod
    def from_env(cls) -> "AppConfig":
        default_log_dir = Path(__file__).resolve().parent.parent / "logs"

        return cls(
            domain_id=os.getenv("SOUTHNOTARY_DOMAIN_ID", DEFAULT_DOMAIN_ID),
            base_url=os.getenv("SOUTHNOTARY_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            api_host=os.getenv("SOUTHNOTARY_API_HOST", DEFAULT_API_HOST),
            credentials=ApiCredentials(
                appid=_get_required_env("SOUTHNOTARY_APPID"),
                randkey=_get_required_env("SOUTHNOTARY_RANDKEY"),
                hashval=_get_required_env("SOUTHNOTARY_HASHVAL"),
            ),
            storage=StorageConfig(
                access_key=_get_required_env("OOS_ACCESS_KEY"),
                secret_key=_get_required_env("OOS_SECRET_KEY"),
                endpoint=os.getenv("OOS_ENDPOINT", DEFAULT_OOS_ENDPOINT),
                bucket=os.getenv("OOS_BUCKET", DEFAULT_OOS_BUCKET),
                object_key_prefix=os.getenv("OOS_OBJECT_KEY_PREFIX", DEFAULT_OBJECT_KEY_PREFIX),
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
                connect_timeout_seconds=_get_int_env("MYSQL_CONNECT_TIMEOUT_SECONDS", 10),
            ),
            evidence_fetch_interval_seconds=_get_int_env(
                "EVIDENCE_FETCH_INTERVAL_SECONDS",
                DEFAULT_EVIDENCE_FETCH_INTERVAL_SECONDS,
            ),
            upload_interval_seconds=_get_int_env("UPLOAD_INTERVAL_SECONDS", DEFAULT_UPLOAD_INTERVAL_SECONDS),
            http_timeout_seconds=_get_int_env("HTTP_TIMEOUT_SECONDS", DEFAULT_HTTP_TIMEOUT_SECONDS),
            api_retry_count=_get_int_env("API_RETRY_COUNT", DEFAULT_API_RETRY_COUNT),
            api_retry_backoff_seconds=_get_float_env(
                "API_RETRY_BACKOFF_SECONDS",
                DEFAULT_API_RETRY_BACKOFF_SECONDS,
            ),
            verify_ssl=_get_bool_env("HTTP_VERIFY_SSL", True),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            log_dir=Path(os.getenv("LOG_DIR", str(default_log_dir))),
        )

    def as_safe_dict(self) -> dict[str, object]:
        """Return a redacted config summary for doctor/health output."""
        return {
            "domain_id": self.domain_id,
            "base_url": self.base_url,
            "api_host": self.api_host,
            "storage": {
                "endpoint": self.storage.endpoint,
                "bucket": self.storage.bucket,
                "object_key_prefix": self.storage.object_key_prefix,
            },
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "user": self.database.user,
                "database": self.database.database,
                "charset": self.database.charset,
            },
            "evidence_fetch_interval_seconds": self.evidence_fetch_interval_seconds,
            "upload_interval_seconds": self.upload_interval_seconds,
            "http_timeout_seconds": self.http_timeout_seconds,
            "api_retry_count": self.api_retry_count,
            "verify_ssl": self.verify_ssl,
            "log_level": self.log_level,
            "log_dir": str(self.log_dir),
        }
