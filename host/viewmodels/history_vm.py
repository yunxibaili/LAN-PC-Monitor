# -*- coding: utf-8 -*-
"""
HistoryViewModel —— 历史趋势数据转换层（v5.2 Phase 5-4）。

职责：
  - 封装 HistoryFacade 查询调用
  - 提供 load(node_id, metric, start, end) 接口
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
    "5m": 5 * 60,
    "30m": 30 * 60,
    "1h": 60 * 60,
    "6h": 6 * 60 * 60,
    "24h": 24 * 60 * 60,
}


class HistoryViewModel:
    """历史趋势数据转换层。"""

    data_changed = Signal()   # 数据刷新
    load_error = Signal(str)  # 加载失败

    def __init__(self, facade: HistoryFacade):
        self._facade = facade
        self._current_node = ""
        self._current_metric = ""
        self._records = []

    def load(self, node_id: str, metric: str,
             start: float = 0, end: float = None,
             limit: int = 1000) -> None:
        """加载历史数据。"""
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
        """返回当前记录列表（MetricRecord, 兼容 ChartWidget）。"""
        return list(self._records)

    def get_summary(self) -> dict:
        """返回聚合统计。"""
        if not self._records:
            return {"avg": None, "min": None, "max": None, "count": 0}
        values = [r.value for r in self._records]
        return {
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "count": len(values),
        }

    def get_range_preset(self, key: str) -> tuple:
        """获取时间范围预设（start, end）。"""
        seconds = RANGE_PRESETS.get(key, 3600)
        end = time.time()
        return (end - seconds, end)

    @staticmethod
    def range_presets():
        """返回可用时间范围列表。"""
        return list(RANGE_PRESETS.keys())
