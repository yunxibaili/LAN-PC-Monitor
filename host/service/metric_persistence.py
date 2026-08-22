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
import threading

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
    """Runtime Frame → Storage Record 转换与写入（带缓冲批合并）。

    性能优化：不再每帧立即 commit，而是把转换后的 MetricRecord 累积到内存缓冲区，
    达到批量阈值或时间窗口后合并为一次 executemany + commit。
    大幅降低 SQLite 事务/fsync 频率（Host 端 CPU 优化）。
    线程安全：persist_frame 可能被本机节点线程/远程 WS 线程调用，用锁保护缓冲。
    """

    def __init__(self, metrics_repo: MetricsRepository,
                 max_batch: int = 200, max_interval: float = 2.0):
        self._repo = metrics_repo
        self._max_batch = max_batch
        self._max_interval = max_interval
        self._buffer: list = []
        self._last_flush = 0.0
        self._lock = threading.Lock()

    def persist_frame(self, node_id: str, frame: dict, ts: float = None) -> int:
        """将一帧 monitor_data 转换并加入缓冲。返回本帧转换记录数（非立即落库数）。"""
        if not frame or not isinstance(frame, dict):
            return 0
        records = self._convert(node_id, frame, ts)
        if not records:
            return 0
        import time as _t
        with self._lock:
            self._buffer.extend(records)
            now = _t.time()
            if len(self._buffer) >= self._max_batch \
                    or (self._last_flush and now - self._last_flush >= self._max_interval):
                self._flush_locked()
            elif self._last_flush == 0.0:
                self._last_flush = now
        return len(records)

    def flush(self) -> int:
        """立即提交所有缓冲记录（供定时器/关闭时调用）。返回写入数。"""
        with self._lock:
            return self._flush_locked()

    def _flush_locked(self) -> int:
        """（持锁调用）合并提交缓冲。"""
        if not self._buffer:
            return 0
        records = self._buffer
        self._buffer = []
        self._last_flush = __import__("time").time()
        try:
            self._repo.insert_batch(records)
            return len(records)
        except Exception as e:
            log.warning("Metric persist failed for %d records: %s", len(records), e)
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
