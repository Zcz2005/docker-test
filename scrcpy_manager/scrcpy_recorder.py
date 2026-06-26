from __future__ import annotations

import datetime as dt
import logging
import os
import signal
import socket
import subprocess
import threading
import time
import uuid
from pathlib import Path

from .config import PathsConfig, RecordingConfig
from .logging_setup import BeijingTimeFormatter


logger = logging.getLogger(__name__)


class ScrcpyRecorder:
    def __init__(
        self,
        device_id: str,
        paths: PathsConfig,
        recording: RecordingConfig,
        task_id: int | None = None,
    ):
        self.paths = paths
        self.recording = recording
        self.device_id = device_id
        self.task_id = task_id
        self.scrcpy_process: subprocess.Popen[str] | None = None
        self.output_thread: threading.Thread | None = None
        self.process_logger: logging.Logger | None = None
        self.record_file: str | None = None
        self.is_recording = False
        self.audio_capture_failed = False
        self.port = self._get_unique_port()

    def _get_unique_port(self) -> int:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("localhost", 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

    def _send_sigint(self) -> bool:
        if not self.scrcpy_process:
            return False
        try:
            os.kill(self.scrcpy_process.pid, signal.SIGINT)
            return True
        except OSError as exc:
            logger.error("发送SIGINT失败: %s", exc)
            return False

    def _force_terminate(self) -> bool:
        if not self.scrcpy_process:
            return False
        try:
            os.kill(self.scrcpy_process.pid, signal.SIGKILL)
            return True
        except OSError as exc:
            logger.error("强制终止失败: %s", exc)
            return False

    def _get_device_serial(self) -> str:
        cmd = [self.paths.adb, "-s", self.device_id, "shell", "getprop", "ro.serialno"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, encoding="utf-8")
            if result.returncode != 0:
                logger.error("获取设备序列号失败: %s", result.stderr.strip())
                return ""
            serial = result.stdout.strip()
            if serial:
                logger.info("设备 %s 序列号: %s", self.device_id, serial)
            return serial
        except (subprocess.TimeoutExpired, OSError) as exc:
            logger.error("获取设备序列号异常: %s", exc)
            return ""

    def start(self) -> bool:
        if self.is_recording:
            logger.warning("录屏已在运行")
            return False

        if not Path(self.paths.scrcpy).exists():
            logger.error("scrcpy路径不存在: %s", self.paths.scrcpy)
            return False

        self.audio_capture_failed = False
        device_serial = self._get_device_serial() or self.device_id.replace(":", "_").replace(".", "_")
        timestamp = time.strftime("%Y%m%d%H%M")
        guid = uuid.uuid4().hex
        self.record_file = str(
            self.paths.recordings / f"recording_{timestamp}_{device_serial}_{guid}.mp4"
        )
        logger.info("录屏文件: %s", self.record_file)

        command = [
            self.paths.scrcpy,
            "-s",
            self.device_id,
            "--record",
            self.record_file,
            "--no-window",
            "--max-size",
            self.recording.max_size,
            "--video-bit",
            self.recording.video_bit,
            "--max-fps",
            self.recording.max_fps,
            "--require-audio",
            "--no-audio-playback",
            "--audio-codec",
            self.recording.audio_codec,
            "--audio-source",
            self.recording.audio_source,
            "--audio-bit-rate",
            self.recording.audio_bit,
            "--port",
            str(self.port),
        ]

        try:
            self.scrcpy_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            logger.error("启动scrcpy失败: %s", exc)
            self._cleanup_resources()
            return False

        log_identifier = f"task_{self.task_id}" if self.task_id is not None else f"scrcpy_{self.scrcpy_process.pid}"
        time_prefix = dt.datetime.now().strftime("%Y%m%d%H")
        self.process_logger = logging.getLogger(f"{time_prefix}_{log_identifier}")
        file_handler = logging.FileHandler(self.paths.logs / f"{time_prefix}_{log_identifier}.log")
        file_handler.setFormatter(BeijingTimeFormatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.process_logger.addHandler(file_handler)
        self.process_logger.setLevel(logging.INFO)

        def read_output() -> None:
            if not self.scrcpy_process or not self.scrcpy_process.stdout:
                return
            while True:
                line = self.scrcpy_process.stdout.readline()
                if not line:
                    if self.scrcpy_process.poll() is not None:
                        break
                    time.sleep(0.1)
                    continue
                line = line.strip()
                logger.info("[scrcpy] %s", line)
                if self.process_logger:
                    self.process_logger.info(line)
                if "ERROR: Failed to start audio capture" in line or "audio capture must be started in the foreground" in line:
                    self.audio_capture_failed = True

        self.output_thread = threading.Thread(target=read_output, daemon=True)
        self.output_thread.start()
        self.is_recording = True
        logger.info("录屏已开始, PID=%s", self.scrcpy_process.pid)
        return True

    def stop(self) -> bool:
        if not self.is_recording:
            return False

        success = False
        try:
            self._send_sigint()
            start_wait = time.time()
            while self.scrcpy_process and self.scrcpy_process.poll() is None:
                if time.time() - start_wait > 15:
                    self._force_terminate()
                    break
                time.sleep(0.2)

            if self.scrcpy_process and (self.scrcpy_process.poll() == 0 or (self.record_file and os.path.exists(self.record_file))):
                success = True
            elif self.record_file and os.path.exists(self.record_file):
                success = True

            if self.output_thread and self.output_thread.is_alive():
                self.output_thread.join(timeout=3)

            if self.recording.boost_volume and success and self.record_file and os.path.exists(self.record_file):
                self._maybe_boost_volume()

            return success
        finally:
            self._cleanup_resources()

    def _maybe_boost_volume(self) -> None:
        assert self.record_file is not None
        directory = Path(self.record_file).parent
        stem = Path(self.record_file).stem
        boosted = directory / f"{stem}_boosted.mp4"
        if self._boost_volume(self.record_file, str(boosted), self.recording.volume_boost):
            try:
                os.remove(self.record_file)
                os.rename(boosted, self.record_file)
            except OSError:
                self.record_file = str(boosted)

    def _boost_volume(self, input_file: str, output_file: str, volume_multiplier: float) -> bool:
        cmd = [
            "ffmpeg",
            "-i",
            input_file,
            "-filter:a",
            f"volume={volume_multiplier}",
            "-c:v",
            "copy",
            "-y",
            output_file,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            if result.returncode == 0:
                logger.info("音量增强完成: %s", output_file)
                return True
            logger.error("音量增强失败: %s", result.stderr)
        except FileNotFoundError:
            logger.error("未找到 ffmpeg，请安装: sudo apt install ffmpeg")
        except subprocess.TimeoutExpired:
            logger.error("音量增强超时")
        return False

    def _cleanup_resources(self) -> None:
        if self.process_logger:
            for handler in self.process_logger.handlers[:]:
                handler.close()
                self.process_logger.removeHandler(handler)
        self.process_logger = None
        self.scrcpy_process = None
        self.output_thread = None
        self.is_recording = False

    def run(self, duration: int, external_task=None) -> tuple[bool, bool, str | None]:
        for attempt in range(1, self.recording.max_retries + 1):
            logger.info("自动录屏尝试 %s/%s，持续 %s 秒", attempt, self.recording.max_retries, duration)
            if not self.start():
                time.sleep(attempt)
                continue

            time.sleep(3)
            if self.audio_capture_failed:
                logger.error("音频捕获失败，准备重试")
                self.stop()
                time.sleep(attempt)
                continue

            task_result: list[bool | None] = [None]
            worker: threading.Thread | None = None
            if external_task is not None and hasattr(external_task, "run_task"):
                def task_wrapper() -> None:
                    try:
                        task_result[0] = bool(external_task.run_task())
                    except Exception as exc:
                        logger.exception("外部任务执行异常: %s", exc)
                        task_result[0] = False

                worker = threading.Thread(target=task_wrapper, daemon=True)
                worker.start()

            if worker:
                worker.join(timeout=max(duration + 60, 360))
                if worker.is_alive():
                    logger.warning("外部任务超时")
                    task_success = False
                else:
                    task_success = task_result[0] is True
            else:
                time.sleep(duration)
                task_success = True

            recording_success = self.stop()
            return recording_success, task_success, self.record_file

        return False, False, self.record_file
