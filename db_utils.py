from __future__ import annotations

import os
from typing import Any, Iterable, Optional, Union

from southnotary_uploader.config import DatabaseConfig
from southnotary_uploader.db_utils import MySQLConnector as _PackageMySQLConnector


class MySQLConnector:
    """Compatibility wrapper for legacy keyword-arg usage and DatabaseConfig."""

    def __init__(self, config: Union[DatabaseConfig, None] = None, **kwargs: Any):
        if config is not None and kwargs:
            raise TypeError("Pass either DatabaseConfig or keyword arguments, not both")
        if config is not None:
            self._connector = _PackageMySQLConnector(config)
        else:
            self._connector = _PackageMySQLConnector(
                DatabaseConfig(
                    host=kwargs.get("host", os.getenv("MYSQL_HOST", "localhost")),
                    port=int(kwargs.get("port", os.getenv("MYSQL_PORT", "3306"))),
                    user=kwargs.get("user", os.getenv("MYSQL_USER", "root")),
                    password=kwargs.get("password", os.getenv("MYSQL_PASSWORD", "")),
                    database=kwargs.get("database", os.getenv("MYSQL_DATABASE", "")),
                    charset=kwargs.get("charset", os.getenv("MYSQL_CHARSET", "utf8mb4")),
                )
            )

    def __enter__(self) -> "MySQLConnector":
        self._connector.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._connector.__exit__(exc_type, exc_value, traceback)

    def execute_query(self, sql: str, params: Optional[Iterable[Any]] = None) -> list[dict[str, Any]]:
        return self._connector.execute_query(sql, params)

    def execute_update(self, sql: str, params: Optional[Iterable[Any]] = None) -> int:
        return self._connector.execute_update(sql, params)


__all__ = ["MySQLConnector"]
