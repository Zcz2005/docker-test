import datetime as dt
import os
import unittest
from unittest.mock import patch

from southnotary_uploader.config import AppConfig
from southnotary_uploader.models import ForensicApiTask, ForensicTaskRecord, UploadCallbackPayload
from southnotary_uploader.object_key import build_object_key
from southnotary_uploader.utils import extract_xiuse_room_id, format_datetime, is_success_code


class HelperTests(unittest.TestCase):
    def test_success_code_accepts_string_and_int(self):
        self.assertTrue(is_success_code("200"))
        self.assertTrue(is_success_code(200))
        self.assertFalse(is_success_code(500))

    def test_format_datetime(self):
        value = dt.datetime(2026, 6, 26, 2, 49, 0)
        self.assertEqual(format_datetime(value), "2026-06-26 02:49:00")
        self.assertEqual(format_datetime(None), "")
        self.assertEqual(format_datetime("already formatted"), "already formatted")

    def test_extract_xiuse_room_id_from_url_when_zero(self):
        self.assertEqual(
            extract_xiuse_room_id("0", "https://example.com/live/123456", "task-1"),
            "123456",
        )
        self.assertEqual(extract_xiuse_room_id("99", "https://example.com/live/123456", "task-1"), "99")


class ObjectKeyTests(unittest.TestCase):
    def test_build_object_key(self):
        fixed_now = dt.datetime(2026, 6, 26, 12, 30, 45)
        key = build_object_key("/data/video/demo.mp4", now=fixed_now)
        expected = (
            f"evidenceProd/Casefile/File/2026-06-26/{int(fixed_now.timestamp())}/demo.mp4"
        )
        self.assertEqual(key, expected)

    def test_custom_prefix(self):
        fixed_now = dt.datetime(2026, 6, 26, 12, 30, 45)
        key = build_object_key("/data/video/demo.mp4", prefix="custom/prefix", now=fixed_now)
        self.assertTrue(key.startswith("custom/prefix/2026-06-26/"))


class ModelTests(unittest.TestCase):
    def test_forensic_api_task_from_api(self):
        task = ForensicApiTask.from_api(
            {
                "taskId": "T1",
                "platform": "22",
                "roomId": "0",
                "url": "https://example.com/999",
                "caseNum": "C1",
            }
        )
        self.assertEqual(task.task_id, "T1")
        self.assertEqual(task.platform, "22")
        self.assertEqual(task.room_id, "0")

    def test_upload_callback_payload(self):
        payload = UploadCallbackPayload(
            obs_path="path/key.mp4",
            case_num="C1",
            task_id="T1",
            screen_start_time="2026-06-26 01:00:00",
            screen_end_time="2026-06-26 02:00:00",
            file_hash="abc",
        )
        self.assertEqual(payload.as_dict()["hash"], "abc")

    def test_forensic_task_record_from_row(self):
        record = ForensicTaskRecord.from_row({"id": 7, "taskid": "T7", "videopath": "/a.mp4"})
        self.assertEqual(record.id, 7)
        self.assertEqual(record.taskid, "T7")


class ConfigTests(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "SOUTHNOTARY_APPID": "app",
            "SOUTHNOTARY_RANDKEY": "rk",
            "SOUTHNOTARY_HASHVAL": "hv",
            "OOS_ACCESS_KEY": "ak",
            "OOS_SECRET_KEY": "sk",
            "MYSQL_HOST": "localhost",
            "MYSQL_USER": "user",
            "MYSQL_PASSWORD": "pass",
            "MYSQL_DATABASE": "db",
            "OOS_OBJECT_KEY_PREFIX": "custom/prefix",
        },
        clear=True,
    )
    def test_config_from_env(self):
        config = AppConfig.from_env()
        self.assertEqual(config.domain_id, "southnotary")
        self.assertEqual(config.storage.object_key_prefix, "custom/prefix")
        self.assertEqual(config.database.host, "localhost")

    def test_missing_required_env_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                AppConfig.from_env()


if __name__ == "__main__":
    unittest.main()
