# -*- coding: utf-8 -*-
"""
Schema —— 数据库表定义与版本管理（v5.2 Phase 5-1）。

职责：
  - 定义所有表结构
  - schema version 管理
  - 表创建 / 迁移入口

不负责：
  - 数据读写（由 Repository 负责）
  - 连接管理（由 Database 负责）
"""

SCHEMA_VERSION = 1

TABLES = {
    "schema_version": """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """,
    "metrics": """
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL NOT NULL,
            timestamp REAL NOT NULL
        )
    """,
    "alerts": """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            node_alias TEXT DEFAULT '',
            name TEXT NOT NULL,
            path TEXT DEFAULT '',
            value REAL,
            threshold REAL,
            level TEXT NOT NULL DEFAULT 'warn',
            timestamp REAL NOT NULL
        )
    """,
    "sessions": """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            snapshot TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    """,
}

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_metrics_node_ts ON metrics(node_id, timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_metrics_node_metric ON metrics(node_id, metric)",
    "CREATE INDEX IF NOT EXISTS idx_metrics_ts ON metrics(timestamp)",  # 5.1: retention 加速
    "CREATE INDEX IF NOT EXISTS idx_alerts_node_ts ON alerts(node_id, timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_level ON alerts(level)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_ts ON alerts(timestamp)",    # 5.1: retention 加速
    "CREATE INDEX IF NOT EXISTS idx_sessions_node_ts ON sessions(node_id, timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_sessions_ts ON sessions(timestamp)", # 5.1: retention 加速
]


def init_schema(conn) -> int:
    """初始化数据库 schema，返回当前版本号。"""
    cursor = conn.cursor()
    for name, ddl in TABLES.items():
        cursor.execute(ddl)
    for idx in INDEXES:
        cursor.execute(idx)
    # 检查或写入版本
    cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
    row = cursor.fetchone()
    if row is None:
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
        conn.commit()
        return SCHEMA_VERSION
    conn.commit()
    return row[0]


def check_version(conn) -> int:
    """检查当前 schema 版本。"""
    cursor = conn.cursor()
    cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
    row = cursor.fetchone()
    return row[0] if row else 0
