# -*- coding: utf-8 -*-
"""
MetricPersistenceService —— 指标持久化服务（v5.2 Phase 5-2）。

职责：
  - 接收 Runtime monitor_data 帧
  - 转换为 MetricRecord 列表
  - batch 写入 MetricsRepository

不负责：
  - UI 数据转换
  - 查询 / 聚合
  - 图表渲染
  - retention 清理
  - Collector 管理
"""
import logging

from host.storage.records import MetricRecord
from host.storage.repositories.metrics_repo import MetricsRepository

log = logging.getLogger("host.service.metric_persistence")

# 帧字段 → Metric 名映射
_FRAME_METRICS = {
    ("cpu", "total_usage"):       "cpu.usage",
    ("cpu", "package_temp_c"):    "cpu.temp",
    ("cpu", "power_w"):           "cpu.power",
    ("gpu", "usage_percent"):     "gpu.usage",
    ("gpu", "core_temp_c"):       "gpu.temp",
    ("gpu", "power_w"):           "gpu.power",
    ("ram", "usage_percent"):     "ram.usage",
    ("net", "upload_mb_s"):       "net.upload",
    ("net", "download_mb_s"):     "net.download",
    ("net_quality", "quality_score"): "net.score",
    ("fps", "fps"):               "fps.value",
    ("fps", "frame_time_ms"):     "fps.frame_time",
}


class MetricPersistenceService:
    """Runtime Frame → Storage Record 转换与写入。"""

    def __init__(self, metrics_repo: MetricsRepository):
        self._repo = metrics_repo

    def persist_frame(self, node_id: str, frame: dict, ts: float = None) -> int:
        """将一帧 monitor_data 转换并持久化。返回写入记录数。"""
        if not frame or not isinstance(frame, dict):
            return 0
        records = self._convert(node_id, frame, ts)
        if not records:
            return 0
        try:
            self._repo.insert_batch(records)
            return len(records)
        except Exception as e:
            log.warning("Metric persist failed for %s: %s", node_id, e)
            return 0

    def _convert(self, node_id: str, frame: dict, ts: float = None) -> list[MetricRecord]:
        """帧 → MetricRecord 列表。"""
        if ts is None:
            ts = frame.get("ts", 0.0)
        records = []
        for (section, field), metric_name in _FRAME_METRICS.items():
            section_data = frame.get(section, {})
            if not isinstance(section_data, dict):
                continue
            value = section_data.get(field)
            if value is None or value == "N/A":
                continue
            try:
                value = float(value)
            except (TypeError, ValueError):
                continue
            records.append(MetricRecord(
                node_id=node_id,
                metric=metric_name,
                value=value,
                timestamp=ts,
            ))
        return records
