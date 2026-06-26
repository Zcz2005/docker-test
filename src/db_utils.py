import logging
from typing import Any, List, Optional, Tuple

import pymysql
from pymysql.cursors import DictCursor

from src.config import (
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)

logger = logging.getLogger(__name__)


class MySQLConnector:
    """MySQL connection helper with context manager support."""

    def __init__(self) -> None:
        self.connection: Optional[pymysql.connections.Connection] = None

    def __enter__(self) -> "MySQLConnector":
        self.connection = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.connection:
            if exc_type:
                self.connection.rollback()
            else:
                self.connection.commit()
            self.connection.close()
            self.connection = None

    def execute_query(
        self, sql: str, params: Optional[Tuple[Any, ...]] = None
    ) -> List[dict]:
        if not self.connection:
            raise RuntimeError("Database connection is not open")

        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())

    def execute_update(
        self, sql: str, params: Optional[Tuple[Any, ...]] = None
    ) -> int:
        if not self.connection:
            raise RuntimeError("Database connection is not open")

        with self.connection.cursor() as cursor:
            affected = cursor.execute(sql, params)
            self.connection.commit()
            return affected
