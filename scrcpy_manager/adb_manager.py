from __future__ import annotations

import logging
import os
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .config import DevicesConfig, PathsConfig


logger = logging.getLogger(__name__)


class AdbManager:
    def __init__(self, paths: PathsConfig, devices: DevicesConfig):
        self.adb_path = paths.adb
        self.devices = devices

    def run_adb_command(self, cmd: list[str], capture_output: bool = True) -> subprocess.CompletedProcess[str]:
        if not Path(self.adb_path).exists():
            message = f"ADB路径不存在: {self.adb_path}"
            logger.error(message)
            return subprocess.CompletedProcess([self.adb_path, *cmd], returncode=1, stdout="", stderr=message)

        full_cmd = [self.adb_path, *cmd]
        try:
            return subprocess.run(full_cmd, capture_output=capture_output, text=True, encoding="utf-8")
        except FileNotFoundError as exc:
            logger.error("运行ADB命令失败: %s", exc)
            return subprocess.CompletedProcess(full_cmd, returncode=1, stdout="", stderr=str(exc))

    def get_connected_devices(self) -> list[str]:
        result = self.run_adb_command(["devices"])
        if result.returncode != 0:
            logger.error("获取设备列表失败: %s", result.stderr)
            return []

        devices: list[str] = []
        for line in result.stdout.strip().splitlines()[1:]:
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) == 2 and parts[1] == "device":
                devices.append(parts[0])
        return devices

    def _check_ip(self, ip: str) -> tuple[str, int] | None:
        for port in self.devices.ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.devices.timeout)
            try:
                if sock.connect_ex((ip, port)) == 0:
                    logger.info("发现WiFi设备: %s:%s", ip, port)
                    return ip, port
            finally:
                sock.close()
        return None

    def discover_wifi_devices(self) -> list[tuple[str, int]]:
        discovered: list[tuple[str, int]] = []
        ips = [f"{self.devices.network_range}{index}" for index in range(1, 255)]

        with ThreadPoolExecutor(max_workers=self.devices.scan_workers) as executor:
            futures = {executor.submit(self._check_ip, ip): ip for ip in ips}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    discovered.append(result)
        return discovered

    def connect_wifi_device(self, ip: str, port: int = 5555) -> bool:
        device_id = f"{ip}:{port}"
        result = self.run_adb_command(["connect", device_id])
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        if result.returncode == 0 and "connected to" in stdout:
            logger.info("成功连接WiFi设备: %s", device_id)
            return True
        logger.error("连接WiFi设备失败: %s, 输出: %s, 错误: %s", device_id, stdout, stderr)
        return False

    def disconnect_device(self, device_id: str) -> bool:
        result = self.run_adb_command(["disconnect", device_id])
        if result.returncode == 0:
            logger.info("成功断开设备: %s", device_id)
            return True
        logger.error("断开设备失败: %s, 错误: %s", device_id, result.stderr)
        return False

    def setup_wifi_devices(self) -> list[str]:
        connected_devices = set(self.get_connected_devices())
        for ip, port in self.discover_wifi_devices():
            device_id = f"{ip}:{port}"
            if device_id not in connected_devices and self.connect_wifi_device(ip, port):
                connected_devices.add(device_id)

        for device in self.devices.manual_devices:
            if device in connected_devices:
                continue
            if ":" in device:
                ip, port = device.split(":", 1)
                if self.connect_wifi_device(ip, int(port)):
                    connected_devices.add(device)

        return self.get_connected_devices()
