"""
MySQL 连接工具（兼容原始脚本调用方式）

支持：
    with MySQLConnector() as db: ...
    with MySQLConnector(host=..., user=..., password=..., database=...) as db: ...

无参调用时从环境变量读取：
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_CHARSET
"""

from __future__ import annotations

import os
from typing import Any, Iterable, Optional


class MySQLConnector:
    def __init__(
        self,
        host: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        port: Optional[int] = None,
        charset: Optional[str] = None,
    ):
        self.host = host or os.getenv("MYSQL_HOST", "localhost")
        self.user = user or os.getenv("MYSQL_USER", "root")
        self.password = password if password is not None else os.getenv("MYSQL_PASSWORD", "")
        self.database = database or os.getenv("MYSQL_DATABASE", "")
        self.port = int(port if port is not None else os.getenv("MYSQL_PORT", "3306"))
        self.charset = charset or os.getenv("MYSQL_CHARSET", "utf8mb4")
        self.connection = None

    def __enter__(self) -> "MySQLConnector":
        try:
            import pymysql
            from pymysql.cursors import DictCursor
        except ImportError as exc:
            raise RuntimeError("请先安装 PyMySQL: pip install PyMySQL") from exc

        if not self.database:
            raise RuntimeError("未配置 MYSQL_DATABASE 环境变量")

        self.connection = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset=self.charset,
            cursorclass=DictCursor,
            autocommit=False,
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def execute_query(self, sql: str, params: Optional[Iterable[Any]] = None) -> list[dict[str, Any]]:
        if self.connection is None:
            raise RuntimeError("数据库连接未打开")
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())

    def execute_update(self, sql: str, params: Optional[Iterable[Any]] = None) -> int:
        if self.connection is None:
            raise RuntimeError("数据库连接未打开")
        try:
            with self.connection.cursor() as cursor:
                affected = cursor.execute(sql, params)
            self.connection.commit()
            return affected
        except Exception:
            self.connection.rollback()
            raise


__all__ = ["MySQLConnector"]
