# -*- coding: utf-8 -*-
"""
Database —— SQLite 连接管理（v5.2 Phase 5-1）。

职责：
  - SQLite 连接创建 / 生命周期
  - Schema 初始化
  - Transaction helper
  - 连接关闭

不负责：
  - 业务查询（由 Repository 负责）
  - 数据转换（由 VM 负责）
"""
import logging
import sqlite3

from host.storage.schema import init_schema, check_version

log = logging.getLogger("host.storage.database")


class Database:
    """SQLite 连接管理器。"""

    def __init__(self, path: str = ":memory:"):
        """
        :param path: 数据库文件路径。":memory:" 为内存数据库（测试用）。
        """
        self._path = path
        self._conn = None

    def connect(self) -> "Database":
        """打开连接并初始化 schema。"""
        self._conn = sqlite3.connect(self._path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        # P1-4: 性能优化 —— NORMAL 降低 fsync 频率（WAL 已保证崩溃安全）
        self._conn.execute("PRAGMA synchronous=NORMAL")
        # P1-4: 避免 SQLITE_BUSY 死锁（5 秒超时）
        self._conn.execute("PRAGMA busy_timeout=5000")
        version = init_schema(self._conn)
        log.info("Database connected: %s (schema v%d)", self._path, version)
        return self

    def close(self) -> None:
        """关闭连接。"""
        if self._conn:
            self._conn.close()
            self._conn = None
            log.info("Database closed: %s", self._path)

    @property
    def conn(self) -> sqlite3.Connection:
        """获取底层连接（Repository 使用）。"""
        if self._conn is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._conn

    @property
    def version(self) -> int:
        """当前 schema 版本。"""
        if self._conn is None:
            return 0
        return check_version(self._conn)

    def execute(self, sql: str, params=()) -> sqlite3.Cursor:
        """执行 SQL（快捷方法）。"""
        return self.conn.execute(sql, params)

    def executemany(self, sql: str, params_list) -> sqlite3.Cursor:
        """批量执行 SQL。"""
        return self.conn.executemany(sql, params_list)

    def commit(self) -> None:
        """提交事务。"""
        self.conn.commit()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
