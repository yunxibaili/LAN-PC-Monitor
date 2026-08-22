# -*- coding: utf-8 -*-
"""
MonitorViewModel —— Monitor 页面数据转换层（v5.2 Phase 3-5B）。

职责：
  - 从 HistoryStore 提取历史趋势数据
  - 转换为 ChartPoint/MetricSeries（图表可直接渲染）
  - 提供指标列表、节点列表、汇总查询

禁止：
  - 访问 FrameStore
  - 访问 NodeConnection
  - QTimer
"""
import logging
import time

from host.store.signals import Signal

log = logging.getLogger("host.viewmodels.monitor_vm")


# ---------- 数据结构 ----------

class ChartPoint:
    """单个数据点（图表可直接消费）。"""

    __slots__ = ("timestamp", "value")

    def __init__(self, timestamp: float, value: float):
        self.timestamp = timestamp
        self.value = value

    def to_dict(self) -> dict:
        return {"timestamp": self.timestamp, "value": self.value}


class MetricSeries:
    """指标时间序列。"""

    __slots__ = ("node_id", "metric", "points")

    def __init__(self, node_id: str, metric: str, points: list = None):
        self.node_id = node_id
        self.metric = metric
        self.points = points or []


# ---------- 支持指标定义 ----------

METRIC_DEFS = {
    "cpu":      {"label": "CPU 使用率", "unit": "%", "y_range": (0, 100)},
    "gpu":      {"label": "GPU 使用率", "unit": "%", "y_range": (0, 100)},
    "ram":      {"label": "内存使用率", "unit": "%", "y_range": (0, 100)},
    "net_up":   {"label": "上传速度", "unit": "MB/s", "y_range": None},
    "net_down": {"label": "下载速度", "unit": "MB/s", "y_range": None},
    "score":    {"label": "网络评分", "unit": "", "y_range": (0, 100)},
}


# ---------- ViewModel ----------

class MonitorViewModel:
    """
    Monitor 数据转换层。

    - 从 HistoryStore 提取历史趋势
    - 提供指标列表/节点列表/汇总
    - 不访问 FrameStore / NodeConnection
    """

    data_changed = Signal(str)  # node_id（某节点数据变化）

    def __init__(self, history_store, node_store):
        """
        :param history_store: HistoryStore 实例
        :param node_store: NodeStore 实例（查询节点元数据）
        """
        self._history_store = history_store
        self._node_store = node_store
        # P1: 节流 —— 每秒只 emit 一次 data_changed（HistoryStore 每秒 7 指标→7 次 point_added）
        self._last_emit_ts = 0.0

        # 订阅 HistoryStore 信号
        self._history_store.point_added.connect(self._on_point_added)
        self._history_store.node_removed.connect(self._on_node_removed)

    # ---------- 信号回调 ----------

    def _on_point_added(self, node_id: str, metric: str, value: float) -> None:
        """新点写入 → 通知 MonitorPage（节流：每秒最多 1 次，避免 7 指标×每秒 7 次冗余刷新）。"""
        now = time.time()
        if now - self._last_emit_ts < 1.0:
            return
        self._last_emit_ts = now
        self.data_changed.emit(node_id)

    def _on_node_removed(self, node_id: str) -> None:
        """节点移除 → 通知 MonitorPage。"""
        self.data_changed.emit(node_id)

    # ---------- 查询 ----------

    def get_history(self, node_id: str, metric: str,
                    limit: int | None = None) -> list:
        """获取历史数据点列表。"""
        raw = self._history_store.query(node_id, metric, limit)
        return [ChartPoint(timestamp=ts, value=val) for ts, val in raw]

    def get_available_metrics(self, node_id: str) -> list:
        """获取该节点已有的指标名列表。"""
        return self._history_store.metrics(node_id)

    def get_node_ids(self) -> list:
        """获取有历史数据的节点 ID 列表。"""
        # HistoryStore 未提供直接方法，遍历 NodeStore + HistoryStore
        ids = []
        for nid in self._node_store.node_ids():
            if self._history_store.metrics(nid):
                ids.append(nid)
        return ids

    def get_summary(self, node_id: str) -> dict:
        """返回节点汇总信息。"""
        metrics = self._history_store.metrics(node_id)
        point_count = sum(
            len(self._history_store.query(node_id, m))
            for m in metrics
        )
        alias = self._node_store.get_alias(node_id)
        return {
            "node_id": node_id,
            "alias": alias,
            "metrics": metrics,
            "points": point_count,
        }

    # ---------- 刷新 ----------

    def refresh(self, node_id: str | None = None) -> None:
        """触发数据变更信号。"""
        if node_id:
            self.data_changed.emit(node_id)
        else:
            for nid in self.get_node_ids():
                self.data_changed.emit(nid)
