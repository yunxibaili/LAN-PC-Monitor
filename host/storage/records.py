# -*- coding: utf-8 -*-
"""
Records —— 存储层数据模型（v5.2 Phase 5-1）。

与 Runtime Model（MonitorFrame / NodeState / AlertState）分离。
属于 Storage domain，不依赖 PyQt5。
"""
from dataclasses import dataclass, field


@dataclass
class MetricRecord:
    """单条指标历史记录。"""
    node_id: str
    metric: str
    value: float
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "metric": self.metric,
            "value": self.value,
            "timestamp": self.timestamp,
        }


@dataclass
class AlertHistoryRecord:
    """单条告警历史记录。"""
    node_id: str
    node_alias: str
    name: str
    path: str
    value: float | None
    threshold: float | None
    level: str
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_alias": self.node_alias,
            "name": self.name,
            "path": self.path,
            "value": self.value,
            "threshold": self.threshold,
            "level": self.level,
            "timestamp": self.timestamp,
        }


@dataclass
class SessionRecord:
    """节点快照记录。"""
    node_id: str
    snapshot: str  # JSON 字符串
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "snapshot": self.snapshot,
            "timestamp": self.timestamp,
        }
