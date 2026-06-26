from __future__ import annotations

import os
from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path

from southnotary_uploader.config import DatabaseConfig


DEFAULT_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.ini"


@dataclass(frozen=True)
class PathsConfig:
    adb: str
    scrcpy: str
    logs: Path
    recordings: Path


@dataclass(frozen=True)
class DevicesConfig:
    network_range: str
    ports: list[int]
    manual_devices: list[str]
    timeout: float
    scan_workers: int


@dataclass(frozen=True)
class RecordingConfig:
    max_size: str
    video_bit: str
    max_fps: str
    duration: int
    audio_bit: str
    audio_source: str
    audio_codec: str
    boost_volume: bool
    volume_boost: float
    max_retries: int


@dataclass(frozen=True)
class SystemConfig:
    check_interval: int
    error_wait: int
    log_cleanup_interval: int
    log_update_interval: int
    log_retention_days: int
    recording_retention_days: int
    domain_id: str
    allow_mock_tasks: bool


@dataclass(frozen=True)
class ScrcpyManagerConfig:
    paths: PathsConfig
    devices: DevicesConfig
    recording: RecordingConfig
    system: SystemConfig
    database: DatabaseConfig
    target_apps: set[str]

    @classmethod
    def load(cls, config_file: str | Path | None = None) -> "ScrcpyManagerConfig":
        path = Path(config_file or os.getenv("SCRCPY_CONFIG_FILE", DEFAULT_CONFIG_FILE))
        parser = ConfigParser()
        if path.is_file():
            parser.read(path, encoding="utf-8")

        logs_dir = Path(parser.get("paths", "logs", fallback="./logs"))
        recordings_dir = Path(parser.get("paths", "recordings", fallback="./recordings"))

        ports = [int(item.strip()) for item in parser.get("devices", "ports", fallback="5555").split(",") if item.strip()]
        manual_devices = [
            item.strip()
            for item in parser.get("devices", "manual_devices", fallback="").split(",")
            if item.strip()
        ]
        target_apps = {
            item.strip()
            for item in parser.get("tasks", "target_apps", fallback="Ailiao,Baobao,Kuaishou,Kelakela,Yingke,Xiuse").split(",")
            if item.strip()
        }

        return cls(
            paths=PathsConfig(
                adb=parser.get("paths", "adb", fallback="/usr/bin/adb"),
                scrcpy=parser.get("paths", "scrcpy", fallback="/usr/bin/scrcpy"),
                logs=logs_dir,
                recordings=recordings_dir,
            ),
            devices=DevicesConfig(
                network_range=parser.get("devices", "network_range", fallback="192.168.31."),
                ports=ports or [5555],
                manual_devices=manual_devices,
                timeout=parser.getfloat("devices", "timeout", fallback=0.5),
                scan_workers=parser.getint("devices", "scan_workers", fallback=64),
            ),
            recording=RecordingConfig(
                max_size=parser.get("recording", "max_size", fallback="1080"),
                video_bit=parser.get("recording", "video_bit", fallback="2M"),
                max_fps=parser.get("recording", "max_fps", fallback="30"),
                duration=parser.getint("recording", "duration", fallback=320),
                audio_bit=parser.get("recording", "audio_bit", fallback="320K"),
                audio_source=parser.get("recording", "audio_source", fallback="output"),
                audio_codec=parser.get("recording", "audio_codec", fallback="aac"),
                boost_volume=parser.getboolean("recording", "boost_volume", fallback=True),
                volume_boost=parser.getfloat("recording", "volume_boost", fallback=3.0),
                max_retries=parser.getint("recording", "max_retries", fallback=3),
            ),
            system=SystemConfig(
                check_interval=parser.getint("system", "check_interval", fallback=6),
                error_wait=parser.getint("system", "error_wait", fallback=10),
                log_cleanup_interval=parser.getint("system", "log_cleanup_interval", fallback=3600),
                log_update_interval=parser.getint("system", "log_update_interval", fallback=3600),
                log_retention_days=parser.getint("system", "log_retention_days", fallback=7),
                recording_retention_days=parser.getint("system", "recording_retention_days", fallback=5),
                domain_id=parser.get("system", "domain_id", fallback="southnotary"),
                allow_mock_tasks=parser.getboolean("system", "allow_mock_tasks", fallback=False),
            ),
            database=DatabaseConfig(
                host=parser.get("database", "host", fallback=os.getenv("MYSQL_HOST", "localhost")),
                port=parser.getint("database", "port", fallback=int(os.getenv("MYSQL_PORT", "3306"))),
                user=parser.get("database", "user", fallback=os.getenv("MYSQL_USER", "root")),
                password=parser.get("database", "password", fallback=os.getenv("MYSQL_PASSWORD", "")),
                database=parser.get("database", "database", fallback=os.getenv("MYSQL_DATABASE", "")),
                charset=parser.get("database", "charset", fallback=os.getenv("MYSQL_CHARSET", "utf8mb4")),
            ),
            target_apps=target_apps,
        )

    def ensure_directories(self) -> None:
        self.paths.logs.mkdir(parents=True, exist_ok=True)
        self.paths.recordings.mkdir(parents=True, exist_ok=True)
