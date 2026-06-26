from __future__ import annotations

import hashlib
import json
import logging
import traceback
from pathlib import Path
from typing import Any

from .config import StorageConfig
from .ctyun_patch import patch_ctyun_zos_region_parser


logger = logging.getLogger(__name__)


def calculate_sha256(file_path: str | Path) -> str:
    sha256_hash = hashlib.sha256()
    with Path(file_path).open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


class OOSUploader:
    """Single-file uploader for CTYun OOS/ZOS."""

    def __init__(self, config: StorageConfig):
        self.config = config
        self._exceptions_module = None
        self.client = self._init_client()

    def _init_client(self):
        try:
            import oos
            import ooscore.exceptions as exceptions
            from ooscore.client import Config
        except ImportError as exc:
            raise RuntimeError(
                "CTYun OOS SDK is not installed. Install the SDK that provides "
                "`oos` and `ooscore` before starting this service."
            ) from exc

        patch_ctyun_zos_region_parser()
        self._exceptions_module = exceptions

        endpoint = self.config.endpoint
        if "http" not in endpoint.lower():
            endpoint = f"http://{endpoint}"

        sdk_config = Config(
            endpoint_url=endpoint,
            signature_version=self.config.signature_version,
            s3={"payload_signing_enabled": True},
        )

        try:
            return oos.client(
                service_name=self.config.service_name,
                endpoint_url=endpoint,
                api_version=self.config.api_version,
                access_key_id=self.config.access_key,
                secret_access_key=self.config.secret_key,
                config=sdk_config,
            )
        except Exception as exc:
            logger.error("Client initialization error: %s", exc)
            logger.debug("Client initialization traceback:\n%s", traceback.format_exc())
            raise

    @staticmethod
    def pretty_print(response: Any) -> None:
        print(json.dumps(response, sort_keys=True, indent=4, default=str, ensure_ascii=False))

    def upload_file(
        self,
        local_file_path: str | Path,
        object_key: str,
        storage_class: str = "STANDARD",
        content_type: str = "application/octet-stream",
        data_location: str | None = None,
        forbid_overwrite: bool = False,
    ):
        params = {
            "Bucket": self.config.bucket,
            "Key": object_key,
            "StorageClass": storage_class,
            "ContentType": content_type,
            "ForbidOverWrite": forbid_overwrite,
        }

        if data_location:
            params["DataLocation"] = data_location

        try:
            with Path(local_file_path).open("rb") as data:
                params["Body"] = data
                response = self.client.put_object(**params)
            logger.info("File uploaded successfully: %s -> %s", local_file_path, object_key)
            return response
        except Exception as exc:
            client_error = getattr(self._exceptions_module, "ClientError", None)
            if client_error is not None and isinstance(exc, client_error):
                error = exc.response.get("Error", {})
                metadata = exc.response.get("ResponseMetadata", {})
                logger.error(
                    "OOS upload failed. code=%s message=%s resource=%s request_id=%s",
                    error.get("Code"),
                    error.get("Message"),
                    error.get("Resource"),
                    metadata.get("RequestId"),
                )
                raise

            logger.exception("Unexpected OOS upload error")
            raise
