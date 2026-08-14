# -*- coding: utf-8 -*-
"""
SessionsRepository —— 会话快照数据访问（v5.2 Phase 5-1）。

职责：
  - 记录节点状态快照
  - 查询历史快照

不负责：
  - 实时状态管理
  - 数据采集
"""
import logging

from host.storage.records import SessionRecord

log = logging.getLogger("host.storage.repositories.sessions")


class SessionsRepository:
    """会话快照数据访问层。"""

    def __init__(self, db):
        self._db = db

    def create(self, record: SessionRecord) -> None:
        """记录快照。"""
        self._db.execute(
            "INSERT INTO sessions (node_id, snapshot, timestamp) VALUES (?, ?, ?)",
            (record.node_id, record.snapshot, record.timestamp),
        )
        self._db.commit()

    def query_recent(self, node_id: str = None, limit: int = 50) -> list[SessionRecord]:
        """查询最近 N 条快照。"""
        if node_id:
            rows = self._db.execute(
                "SELECT node_id, snapshot, timestamp FROM sessions "
                "WHERE node_id = ? ORDER BY timestamp DESC LIMIT ?",
                (node_id, limit),
            ).fetchall()
        else:
            rows = self._db.execute(
                "SELECT node_id, snapshot, timestamp FROM sessions "
                "ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [SessionRecord(*row) for row in rows]

    def count(self, node_id: str = None) -> int:
        """计数。"""
        if node_id:
            row = self._db.execute(
                "SELECT COUNT(*) FROM sessions WHERE node_id = ?", (node_id,)
            ).fetchone()
        else:
            row = self._db.execute("SELECT COUNT(*) FROM sessions").fetchone()
        return row[0] if row else 0

    def clear(self, node_id: str = None) -> None:
        """清空快照。"""
        if node_id:
            self._db.execute("DELETE FROM sessions WHERE node_id = ?", (node_id,))
        else:
            self._db.execute("DELETE FROM sessions")
        self._db.commit()

    def delete_before(self, timestamp: float) -> int:
        """删除 timestamp < 给定值 的快照，返回删除数量。"""
        cursor = self._db.execute(
            "DELETE FROM sessions WHERE timestamp < ?", (timestamp,)
        )
        self._db.commit()
        return cursor.rowcount if cursor.rowcount else 0
