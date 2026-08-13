# -*- coding: utf-8 -*-
"""
HistoryStore —— 历史数据缓存 分片状态（v5.2 Phase 0）。

职责：维护每个节点的历史指标点（deque 环形缓冲），供图表消费。
v5.1 无此模块，为 v5.2 Monitor 页图表新增。

- 纯逻辑实现，使用 collections.deque(maxlen) 天然限长，防无限增长。
- 指标按 node_id + metric 维度存储点序列 (timestamp, value)。
- v6 预留：可替换后端为 storage/（SQLite），对外接口保持 push/query。

信号（统一规范）：
    point_added(node_id, metric, value)   新点写入
    node_removed(node_id)                 节点移除清理
    reset()                               整体清空
"""
from collections import defaultdict, deque

from host.store.signals import Signal


class HistoryStore:
    """历史数据缓存 Store。"""

    point_added = Signal(str, str, float)
    node_removed = Signal(str)
    reset = Signal()

    def __init__(self, maxlen: int = 300, minutes: int = 5):
        """
        :param maxlen:  每节点每指标保留点数（默认 300 ≈ 5 分钟 @1s）
        :param minutes: 语义化时长（仅文档/配置，v6 由 storage 保留策略接管）
        """
        self._maxlen = max(10, int(maxlen))
        self._minutes = minutes
        # node_id -> {metric -> deque[(ts, value)]}
        self._data = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=self._maxlen)))

    # ---------- 写入 ----------

    def push(self, node_id: str, metric: str, value, ts: float | None = None) -> None:
        """写入一个历史点。value 非数值（N/A/None）时跳过。"""
        try:
            v = float(value)
        except (TypeError, ValueError):
            return
        import time as _t
        ts = ts if ts is not None else _t.time()
        self._data[node_id][metric].append((ts, v))
        self.point_added.emit(node_id, metric, v)

    def push_frame(self, node_id: str, frame: dict, ts: float | None = None) -> None:
        """从 monitor_data 帧批量提取常用指标写入历史。"""
        extractors = {
            "cpu": ("cpu", "total_usage"),
            "gpu": ("gpu", "usage_percent"),
            "ram": ("ram", "usage_percent"),
            "fps": ("fps", "fps"),
            "score": ("net_quality", "quality_score"),
            "net_up": ("net", "upload_mb_s"),
            "net_down": ("net", "download_mb_s"),
        }
        for metric, (section, key) in extractors.items():
            try:
                value = frame.get(section, {}).get(key)
            except AttributeError:
                continue
            if value in (None, "N/A"):
                continue
            self.push(node_id, metric, value, ts)

    def remove_node(self, node_id: str) -> None:
        """移除节点全部历史（幂等）。"""
        if node_id in self._data:
            del self._data[node_id]
            self.node_removed.emit(node_id)

    def clear(self) -> None:
        self._data.clear()
        self.reset.emit()

    # ---------- 查询 ----------

    def query(self, node_id: str, metric: str,
              limit: int | None = None) -> list:
        """返回该节点某指标的 [(ts, value), ...]，最近优先，可按 limit 截断。"""
        seq = list(self._data.get(node_id, {}).get(metric, []))
        if limit is not None and limit > 0:
            seq = seq[-limit:]
        return seq

    # ---------- 规格别名（v5.2） ----------

    def append(self, node_id: str, metric: str, value,
               ts: float | None = None) -> None:
        """规格要求的接口名，等价 push()。"""
        self.push(node_id, metric, value, ts)

    def get_history(self, node_id: str, metric: str,
                    limit: int | None = None) -> list:
        """规格要求的接口名，等价 query()。"""
        return self.query(node_id, metric, limit)

    def last(self, node_id: str, metric: str):
        """最近一个点的 value；无则 None。"""
        seq = self._data.get(node_id, {}).get(metric)
        return seq[-1][1] if seq else None

    def metrics(self, node_id: str) -> list:
        """该节点已有的指标名列表。"""
        return list(self._data.get(node_id, {}).keys())

    def node_count(self) -> int:
        return len(self._data)

    def point_count(self) -> int:
        """全部节点/指标点数（用于测试/诊断）。"""
        return sum(len(dq) for node in self._data.values()
                   for dq in node.values())

    @property
    def maxlen(self) -> int:
        return self._maxlen
