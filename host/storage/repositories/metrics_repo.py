# -*- coding: utf-8 -*-
"""
MetricsRepository —— 指标历史数据访问（v5.2 Phase 5-1）。

职责：
  - 插入指标记录
  - 范围查询
  - 聚合统计
  - 计数

不负责：
  - 数据转换
  - UI 渲染
"""
import logging

from host.storage.records import MetricRecord

log = logging.getLogger("host.storage.repositories.metrics")


class MetricsRepository:
    """指标历史数据访问层。"""

    def __init__(self, db):
        """
        :param db: Database 实例
        """
        self._db = db

    def insert(self, record: MetricRecord) -> None:
        """插入单条指标记录。"""
        self._db.execute(
            "INSERT INTO metrics (node_id, metric, value, timestamp) VALUES (?, ?, ?, ?)",
            (record.node_id, record.metric, record.value, record.timestamp),
        )
        self._db.commit()

    def insert_batch(self, records: list[MetricRecord]) -> None:
        """批量插入指标记录。"""
        self._db.executemany(
            "INSERT INTO metrics (node_id, metric, value, timestamp) VALUES (?, ?, ?, ?)",
            [(r.node_id, r.metric, r.value, r.timestamp) for r in records],
        )
        self._db.commit()

    def query_range(self, node_id: str, metric: str,
                    start: float = 0, end: float = float("inf"),
                    limit: int = 1000) -> list[MetricRecord]:
        """范围查询：返回指定时间范围内的指标记录。"""
        rows = self._db.execute(
            "SELECT node_id, metric, value, timestamp FROM metrics "
            "WHERE node_id = ? AND metric = ? AND timestamp >= ? AND timestamp <= ? "
            "ORDER BY timestamp ASC LIMIT ?",
            (node_id, metric, start, end, limit),
        ).fetchall()
        return [MetricRecord(*row) for row in rows]

    def latest(self, node_id: str, metric: str,
               limit: int = 300) -> list[MetricRecord]:
        """返回最近 N 条记录（时间倒序，newest → oldest）。"""
        rows = self._db.execute(
            "SELECT node_id, metric, value, timestamp FROM metrics "
            "WHERE node_id = ? AND metric = ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (node_id, metric, limit),
        ).fetchall()
        return [MetricRecord(*row) for row in rows]

    def count(self, node_id: str = None, metric: str = None) -> int:
        """计数。"""
        if node_id and metric:
            row = self._db.execute(
                "SELECT COUNT(*) FROM metrics WHERE node_id = ? AND metric = ?",
                (node_id, metric),
            ).fetchone()
        elif node_id:
            row = self._db.execute(
                "SELECT COUNT(*) FROM metrics WHERE node_id = ?", (node_id,)
            ).fetchone()
        elif metric:
            row = self._db.execute(
                "SELECT COUNT(*) FROM metrics WHERE metric = ?", (metric,)
            ).fetchone()
        else:
            row = self._db.execute("SELECT COUNT(*) FROM metrics").fetchone()
        return row[0] if row else 0

    def aggregate(self, node_id: str, metric: str,
                  start: float = 0, end: float = float("inf")) -> dict:
        """聚合统计：avg / min / max / count。"""
        row = self._db.execute(
            "SELECT AVG(value), MIN(value), MAX(value), COUNT(*) FROM metrics "
            "WHERE node_id = ? AND metric = ? AND timestamp >= ? AND timestamp <= ?",
            (node_id, metric, start, end),
        ).fetchone()
        if row is None or row[3] == 0:
            return {"avg": None, "min": None, "max": None, "count": 0}
        return {"avg": row[0], "min": row[1], "max": row[2], "count": row[3]}

    def nodes(self) -> list[str]:
        """返回所有有指标数据的节点 ID。"""
        rows = self._db.execute(
            "SELECT DISTINCT node_id FROM metrics"
        ).fetchall()
        return [row[0] for row in rows]

    def metrics(self, node_id: str) -> list[str]:
        """返回指定节点的所有指标名。"""
        rows = self._db.execute(
            "SELECT DISTINCT metric FROM metrics WHERE node_id = ?", (node_id,)
        ).fetchall()
        return [row[0] for row in rows]

    def clear(self, node_id: str = None) -> None:
        """清空指标数据。"""
        if node_id:
            self._db.execute("DELETE FROM metrics WHERE node_id = ?", (node_id,))
        else:
            self._db.execute("DELETE FROM metrics")
        self._db.commit()

    def delete_before(self, timestamp: float) -> int:
        """删除 timestamp < 给定值 的记录，返回删除数量（严格小于，保留边界）。"""
        cursor = self._db.execute(
            "DELETE FROM metrics WHERE timestamp < ?", (timestamp,)
        )
        self._db.commit()
        return cursor.rowcount if cursor.rowcount else 0
