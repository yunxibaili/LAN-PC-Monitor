# -*- coding: utf-8 -*-
"""
HistoryViewModel —— 历史趋势数据转换层（v5.3.3 History UX）。

职责：
  - 封装 HistoryFacade 查询调用
  - 单指标 / 多指标加载
  - 统计数据转换（avg/min/max/count）
  - 不直接碰 Repository / SQLite（仅经 Facade）

不负责：
  - UI 布局
  - Chart 渲染
  - retention
"""
import logging
import time

from host.store.signals import Signal
from host.facade.history_facade import HistoryFacade

log = logging.getLogger("host.viewmodels.history_vm")


# 时间范围预设（秒）
RANGE_PRESETS = {
    "10m": 10 * 60,
    "1h": 60 * 60,
    "6h": 6 * 60 * 60,
    "24h": 24 * 60 * 60,
    "7d": 7 * 24 * 60 * 60,
}


class HistoryViewModel:
    """历史趋势数据转换层。"""

    data_changed = Signal()
    load_error = Signal(str)

    def __init__(self, facade: HistoryFacade):
        self._facade = facade
        self._current_node = ""
        self._current_metric = ""
        self._records = []
        # 多指标：{metric_name: [MetricRecord]}
        self._multi_records = {}

    # ---- 单指标（向后兼容） ----

    def load(self, node_id: str, metric: str,
             start: float = 0, end: float = None,
             limit: int = 1000) -> None:
        if not node_id or not metric:
            return
        if end is None:
            end = time.time()
        try:
            self._records = self._facade.query_range(
                node_id, metric, start, end, limit)
            self._current_node = node_id
            self._current_metric = metric
            self.data_changed.emit()
        except Exception as e:
            log.warning("History load failed: %s", e)
            self.load_error.emit(str(e))

    def get_records(self):
        return list(self._records)

    def get_summary(self) -> dict:
        if not self._records:
            return {"avg": None, "min": None, "max": None, "count": 0}
        values = [r.value for r in self._records]
        return {
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "count": len(values),
        }

    # ---- 多指标（v5.3.3 History UX） ----

    def load_multi(self, node_id: str, metrics: list,
                   start: float = 0, end: float = None,
                   limit: int = 1000) -> None:
        """加载多个指标。"""
        if not node_id or not metrics:
            return
        if end is None:
            end = time.time()
        self._multi_records.clear()
        for metric in metrics:
            try:
                records = self._facade.query_range(
                    node_id, metric, start, end, limit)
                self._multi_records[metric] = records
            except Exception as e:
                log.warning("History load %s failed: %s", metric, e)
                self._multi_records[metric] = []
        self._current_node = node_id
        self.data_changed.emit()

    def get_multi_records(self) -> dict:
        """返回 {metric_name: [MetricRecord]}。"""
        return dict(self._multi_records)

    def get_multi_summary(self) -> dict:
        """返回 {metric_name: {avg, min, max, count}}。"""
        result = {}
        for metric, records in self._multi_records.items():
            if not records:
                result[metric] = {"avg": None, "min": None, "max": None, "count": 0}
                continue
            values = [r.value for r in records]
            result[metric] = {
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "count": len(values),
            }
        return result

    # ---- 通用 ----

    def get_range_preset(self, key: str) -> tuple:
        seconds = RANGE_PRESETS.get(key, 3600)
        end = time.time()
        return (end - seconds, end)

    @staticmethod
    def range_presets():
        return list(RANGE_PRESETS.keys())
