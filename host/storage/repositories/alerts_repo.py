# -*- coding: utf-8 -*-
"""
AlertsRepository —— 告警历史数据访问（v5.2 Phase 5-1）。

职责：
  - 插入告警记录
  - 查询最近告警
  - 按等级/节点过滤
  - 计数

不负责：
  - 告警检测（AlertEngine 负责）
  - 告警去重（AlertStore 负责）
"""
import logging

from host.storage.records import AlertHistoryRecord

log = logging.getLogger("host.storage.repositories.alerts")


class AlertsRepository:
    """告警历史数据访问层。"""

    def __init__(self, db):
        self._db = db

    def insert(self, record: AlertHistoryRecord) -> None:
        """插入单条告警记录。"""
        self._db.execute(
            "INSERT INTO alerts (node_id, node_alias, name, path, value, threshold, level, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (record.node_id, record.node_alias, record.name, record.path,
             record.value, record.threshold, record.level, record.timestamp),
        )
        self._db.commit()

    def query_recent(self, limit: int = 100) -> list[AlertHistoryRecord]:
        """查询最近 N 条告警（时间倒序）。"""
        rows = self._db.execute(
            "SELECT node_id, node_alias, name, path, value, threshold, level, timestamp "
            "FROM alerts ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [AlertHistoryRecord(*row) for row in rows]

    def query_by_level(self, level: str, limit: int = 100) -> list[AlertHistoryRecord]:
        """按等级查询。"""
        rows = self._db.execute(
            "SELECT node_id, node_alias, name, path, value, threshold, level, timestamp "
            "FROM alerts WHERE level = ? ORDER BY timestamp DESC LIMIT ?",
            (level, limit),
        ).fetchall()
        return [AlertHistoryRecord(*row) for row in rows]

    def query_by_node(self, node_id: str, limit: int = 100) -> list[AlertHistoryRecord]:
        """按节点查询。"""
        rows = self._db.execute(
            "SELECT node_id, node_alias, name, path, value, threshold, level, timestamp "
            "FROM alerts WHERE node_id = ? ORDER BY timestamp DESC LIMIT ?",
            (node_id, limit),
        ).fetchall()
        return [AlertHistoryRecord(*row) for row in rows]

    def count(self, level: str = None) -> int:
        """计数。"""
        if level:
            row = self._db.execute(
                "SELECT COUNT(*) FROM alerts WHERE level = ?", (level,)
            ).fetchone()
        else:
            row = self._db.execute("SELECT COUNT(*) FROM alerts").fetchone()
        return row[0] if row else 0

    def clear(self) -> None:
        """清空告警历史。"""
        self._db.execute("DELETE FROM alerts")
        self._db.commit()
