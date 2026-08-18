# -*- coding: utf-8 -*-
"""
HistoryFacade —— 历史指标读取门面（v5.2 Phase 5-3 / v5.3.4 降采样）。

职责：
  - 封装 MetricsRepository 的读取接口（range / latest / aggregate）
  - 参数校验
  - 时间桶降采样（长区间自动聚合）

不负责：
  - UI 数据转换
  - Chart 格式化
  - retention
"""
import logging

from host.storage.records import MetricRecord
from host.storage.repositories.metrics_repo import MetricsRepository

log = logging.getLogger("host.facade.history")


class HistoryFacade:
    """历史指标读取门面：Page → (VM) → Facade → Repository → SQLite。"""

    # 降采样阈值：数据点 > max_points 时自动聚合
    MAX_POINTS = 500

    def __init__(self, metrics_repo: MetricsRepository):
        self._repo = metrics_repo

    def _validate(self, node_id: str, metric: str) -> None:
        if not node_id:
            raise ValueError("node_id must not be empty")
        if not metric:
            raise ValueError("metric must not be empty")

    def query_range(self, node_id: str, metric: str,
                    start: float = 0, end: float = float("inf"),
                    limit: int = 1000) -> list[MetricRecord]:
        """时间范围查询（升序）。超长区间自动降采样。"""
        self._validate(node_id, metric)
        records = self._repo.query_range(node_id, metric, start, end, limit)
        if len(records) > self.MAX_POINTS:
            records = self._downsample(records, self.MAX_POINTS)
        return records

    def _downsample(self, records: list, target: int) -> list:
        """时间桶降采样：将 records 聚合到 target 个点（桶内取平均）。"""
        if not records or len(records) <= target:
            return records
        span = records[-1].timestamp - records[0].timestamp
        if span <= 0:
            return records
        bucket_size = span / target
        buckets = []
        current_bucket = []
        bucket_start = records[0].timestamp

        for r in records:
            if r.timestamp - bucket_start >= bucket_size:
                if current_bucket:
                    buckets.append(self._avg_record(current_bucket))
                current_bucket = [r]
                bucket_start = r.timestamp
            else:
                current_bucket.append(r)

        if current_bucket:
            buckets.append(self._avg_record(current_bucket))
        return buckets

    @staticmethod
    def _avg_record(records: list) -> MetricRecord:
        """多条记录聚合为一条（时间取中点，值取平均）。"""
        if len(records) == 1:
            return records[0]
        mid_ts = (records[0].timestamp + records[-1].timestamp) / 2
        avg_val = sum(r.value for r in records) / len(records)
        return MetricRecord(
            node_id=records[0].node_id,
            metric=records[0].metric,
            value=avg_val,
            timestamp=mid_ts,
        )

    def latest(self, node_id: str, metric: str,
               limit: int = 300) -> list[MetricRecord]:
        """最近 N 条（时间倒序）。"""
        self._validate(node_id, metric)
        return self._repo.latest(node_id, metric, limit)

    def aggregate(self, node_id: str, metric: str,
                  start: float = 0, end: float = float("inf")) -> dict:
        """聚合统计（avg/min/max/count）。"""
        self._validate(node_id, metric)
        return self._repo.aggregate(node_id, metric, start, end)
