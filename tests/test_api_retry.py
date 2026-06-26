import unittest
from unittest.mock import MagicMock, patch

import requests

from southnotary_uploader.api import EvidenceApiClient
from southnotary_uploader.config import ApiCredentials


class ApiRetryTests(unittest.TestCase):
    def setUp(self):
        self.credentials = ApiCredentials(appid="a", randkey="r", hashval="h")
        self.client = EvidenceApiClient(
            base_url="https://example.com/api",
            credentials=self.credentials,
            retry_count=3,
            retry_backoff_seconds=0,
        )

    @patch("southnotary_uploader.api.time.sleep")
    def test_get_token_retries_on_request_error(self, sleep_mock):
        ok_response = MagicMock()
        ok_response.raise_for_status.return_value = None
        ok_response.json.return_value = {"code": "200", "token": "t", "expireAt": "x"}

        self.client.session.get = MagicMock(
            side_effect=[
                requests.ConnectionError("temporary"),
                ok_response,
            ]
        )

        result = self.client.get_token()
        self.assertEqual(result["token"], "t")
        self.assertEqual(self.client.session.get.call_count, 2)
        sleep_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
