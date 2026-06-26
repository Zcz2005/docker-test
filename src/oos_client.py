import json
import logging
import traceback

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import oos  # noqa: E402
import ooscore.exceptions as exceptions  # noqa: E402
from ooscore.client import Config  # noqa: E402

from src import oos_patch  # noqa: F401, E402

logger = logging.getLogger(__name__)


class OOSUploader:
    """OOS single file upload client."""

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        endpoint: str,
        bucket: str,
        signature_version: str = "s3",
        service_name: str = "s3",
        api_version: str = "2006-03-01",
    ) -> None:
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint = endpoint
        self.bucket = bucket
        self.signature_version = signature_version
        self.service_name = service_name
        self.api_version = api_version
        self.client = self._init_client()

    def _init_client(self):
        endpoint = self.endpoint
        if "http" not in endpoint.lower():
            endpoint = "http://" + endpoint

        try:
            config = Config(
                endpoint_url=endpoint,
                signature_version=self.signature_version,
                s3={"payload_signing_enabled": True},
            )
            return oos.client(
                service_name=self.service_name,
                endpoint_url=endpoint,
                api_version=self.api_version,
                access_key_id=self.access_key,
                secret_access_key=self.secret_key,
                config=config,
            )
        except Exception as exc:
            logger.error(traceback.format_exc())
            logger.error("Client initialization error: %s", exc)
            raise

    def upload_file(
        self,
        local_file_path: str,
        object_key: str,
        storage_class: str = "STANDARD",
        content_type: str = "application/octet-stream",
        data_location=None,
        forbid_overwrite: bool = False,
    ):
        try:
            params = {
                "Bucket": self.bucket,
                "Key": object_key,
                "StorageClass": storage_class,
                "ContentType": content_type,
                "ForbidOverWrite": forbid_overwrite,
            }

            if data_location:
                params["DataLocation"] = data_location

            with open(local_file_path, "rb") as data:
                params["Body"] = data
                response = self.client.put_object(**params)

            logger.info(
                "File uploaded successfully: %s -> %s", local_file_path, object_key
            )
            return response

        except exceptions.ClientError as exc:
            error_msg = (
                f"\n Response code: {exc.response['Error']['Code']}\n"
                f" Error message: {exc.response['Error']['Message']}\n"
                f" Resource: {exc.response['Error']['Resource']}\n"
                f" request id: {exc.response['ResponseMetadata']['RequestId']}"
            )
            logger.error(error_msg)
            raise
        except Exception as exc:
            logger.error("Upload error: %s", exc)
            traceback.print_exc()
            raise
