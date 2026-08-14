# -*- coding: utf-8 -*-
"""
HistoryFacade —— 历史指标读取门面（v5.2 Phase 5-3）。

职责：
  - 封装 MetricsRepository 的读取接口（range / latest / aggregate）
  - 参数校验

不负责：
  - UI 数据转换
  - Chart 格式化
  - retention
"""
import logging

from host.storage.database import Database
from host.storage.records import MetricRecord
from host.storage.repositories.metrics_repo import MetricsRepository

log = logging.getLogger("host.facade.history")


class HistoryFacade:
    """历史指标读取门面：Page → (VM) → Facade → Repository → SQLite。"""

    def __init__(self, metrics_repo: MetricsRepository):
        self._repo = metrics_repo

    @classmethod
    def from_path(cls, db_path: str) -> "HistoryFacade":
        """从数据库路径创建（内部封装 Database + Repository 生命周期）。"""
        db = Database(db_path)
        db.connect()
        return cls(MetricsRepository(db))

    # ---------- 参数校验 ----------

    def _validate(self, node_id: str, metric: str) -> None:
        """非法查询参数抛 ValueError。"""
        if not node_id:
            raise ValueError("node_id must not be empty")
        if not metric:
            raise ValueError("metric must not be empty")

    # ---------- 查询接口 ----------

    def query_range(self, node_id: str, metric: str,
                    start: float = 0, end: float = float("inf"),
                    limit: int = 1000) -> list[MetricRecord]:
        """时间范围查询（升序）。数据不存在返回 []。"""
        self._validate(node_id, metric)
        return self._repo.query_range(node_id, metric, start, end, limit)

    def latest(self, node_id: str, metric: str,
               limit: int = 300) -> list[MetricRecord]:
        """最近 N 条（时间倒序）。数据不存在返回 []。"""
        self._validate(node_id, metric)
        return self._repo.latest(node_id, metric, limit)

    def aggregate(self, node_id: str, metric: str,
                  start: float = 0, end: float = float("inf")) -> dict:
        """聚合统计（avg/min/max/count）。数据不存在返回 count=0。"""
        self._validate(node_id, metric)
        return self._repo.aggregate(node_id, metric, start, end)
