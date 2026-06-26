import datetime as dt
import unittest

from southnotary_uploader.api import is_success_code
from southnotary_uploader.service import _extract_xiuse_room_id, _format_datetime


class HelperTests(unittest.TestCase):
    def test_success_code_accepts_string_and_int(self):
        self.assertTrue(is_success_code("200"))
        self.assertTrue(is_success_code(200))
        self.assertFalse(is_success_code(500))

    def test_format_datetime(self):
        value = dt.datetime(2026, 6, 26, 2, 49, 0)
        self.assertEqual(_format_datetime(value), "2026-06-26 02:49:00")
        self.assertEqual(_format_datetime(None), "")
        self.assertEqual(_format_datetime("already formatted"), "already formatted")

    def test_extract_xiuse_room_id_from_url_when_zero(self):
        self.assertEqual(
            _extract_xiuse_room_id("0", "https://example.com/live/123456", "task-1"),
            "123456",
        )
        self.assertEqual(_extract_xiuse_room_id("99", "https://example.com/live/123456", "task-1"), "99")


if __name__ == "__main__":
    unittest.main()
