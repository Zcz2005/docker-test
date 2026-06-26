from __future__ import annotations

from typing import Any, Iterable, Optional

from .config import DatabaseConfig


class MySQLConnector:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = None

    def __enter__(self) -> "MySQLConnector":
        try:
            import pymysql
            from pymysql.cursors import DictCursor
        except ImportError as exc:
            raise RuntimeError("PyMySQL is required. Install dependencies from requirements.txt.") from exc

        self.connection = pymysql.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database,
            charset=self.config.charset,
            cursorclass=DictCursor,
            autocommit=False,
            connect_timeout=self.config.connect_timeout_seconds,
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def execute_query(self, sql: str, params: Optional[Iterable[Any]] = None) -> list[dict[str, Any]]:
        if self.connection is None:
            raise RuntimeError("Database connection is not open")

        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())

    def execute_update(self, sql: str, params: Optional[Iterable[Any]] = None) -> int:
        if self.connection is None:
            raise RuntimeError("Database connection is not open")

        try:
            with self.connection.cursor() as cursor:
                affected_rows = cursor.execute(sql, params)
            self.connection.commit()
            return affected_rows
        except Exception:
            self.connection.rollback()
            raise
