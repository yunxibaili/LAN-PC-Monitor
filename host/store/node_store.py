# -*- coding: utf-8 -*-
"""
NodeStore —— 节点连接/状态/RTT/丢包/评分 分片状态（v5.2 Phase 0）。

职责：集中管理每个节点的连接元数据与派生状态，替代 v5.1 MainWindow 中的
`nodes/statuses/rtts/losses/scores/scorers` 散落 dict。

- 纯逻辑实现，不直接持有 NodeConnection（仅存 node_id + 元数据）。
- 连接对象由 MainWindow/Controller 持有，通过 add/remove 通知本 Store。
- 评分（QualityScorer）是有状态对象（滑动窗口），保留在本 Store 内
  `dict[node_id -> QualityScorer]`，不散落到 UI。

信号（统一规范）：
    node_updated(node_id)    节点状态/指标变化
    node_added(node_id)      节点加入
    node_removed(node_id)    节点移除
    reset()                  整体清空
"""
from collections import OrderedDict

from host.store.signals import Signal
from common.quality import QualityScorer


class NodeStore:
    """节点状态分片 Store。"""

    node_updated = Signal(str)        # 通用变更（兼容）
    node_added = Signal(str)          # 节点加入
    node_removed = Signal(str)        # 节点移除
    status_changed = Signal(str, str)  # (node_id, status) 状态变更
    metrics_updated = Signal(str)      # (node_id) 指标（RTT/丢包/评分）更新
    reset = Signal()

    def __init__(self):
        # node_id -> 节点元数据（不存连接对象本身）
        self._nodes = OrderedDict()
        # node_id -> 状态文本（connected/auth_failed/offline...）
        self._statuses = {}
        # node_id -> RTT ms
        self._rtts = {}
        # node_id -> 丢包率 %
        self._losses = {}
        # node_id -> (score, grade)
        self._scores = {}
        # node_id -> QualityScorer（有状态滑动窗口，保留在 Store 内）
        self._scorers = {}

    # ---------- 生命周期 ----------

    def add_node(self, node_id: str, alias: str = "",
                 ip: str = "", port: int = 0) -> None:
        """加入一个节点（幂等：已存在则仅更新元数据）。"""
        existed = node_id in self._nodes
        self._nodes[node_id] = {
            "node_id": node_id,
            "alias": alias or f"{ip}:{port}" or node_id,
            "ip": ip,
            "port": port,
        }
        if node_id not in self._scorers:
            self._scorers[node_id] = QualityScorer()
        if not existed:
            self.node_added.emit(node_id)
        else:
            self.node_updated.emit(node_id)

    def remove_node(self, node_id: str) -> None:
        """移除节点（幂等）。"""
        if node_id not in self._nodes:
            return
        self._nodes.pop(node_id, None)
        self._statuses.pop(node_id, None)
        self._rtts.pop(node_id, None)
        self._losses.pop(node_id, None)
        self._scores.pop(node_id, None)
        self._scorers.pop(node_id, None)
        self.node_removed.emit(node_id)

    def clear(self) -> None:
        """清空全部节点。"""
        self._nodes.clear()
        self._statuses.clear()
        self._rtts.clear()
        self._losses.clear()
        self._scores.clear()
        self._scorers.clear()
        self.reset.emit()

    # ---------- 查询 ----------

    def node_ids(self) -> list:
        return list(self._nodes.keys())

    def count(self) -> int:
        return len(self._nodes)

    def has(self, node_id: str) -> bool:
        return node_id in self._nodes

    def get(self, node_id: str) -> dict | None:
        """返回节点元数据副本；不存在返回 None。"""
        node = self._nodes.get(node_id)
        return dict(node) if node else None

    def get_alias(self, node_id: str) -> str:
        node = self._nodes.get(node_id)
        return node["alias"] if node else node_id

    # ---------- 状态 ----------

    def update_status(self, node_id: str, status: str) -> None:
        self._statuses[node_id] = status
        self.status_changed.emit(node_id, status)
        self.node_updated.emit(node_id)

    def get_status(self, node_id: str) -> str | None:
        return self._statuses.get(node_id)

    # ---------- RTT / 丢包 / 评分 ----------

    def update_rtt(self, node_id: str, rtt_ms: float) -> None:
        self._rtts[node_id] = float(rtt_ms)
        self.metrics_updated.emit(node_id)
        self.node_updated.emit(node_id)

    def get_rtt(self, node_id: str) -> float | None:
        return self._rtts.get(node_id)

    def update_loss(self, node_id: str, loss: float) -> None:
        self._losses[node_id] = float(loss)
        self.metrics_updated.emit(node_id)
        self.node_updated.emit(node_id)

    def get_loss(self, node_id: str) -> float | None:
        return self._losses.get(node_id)

    def update_quality(self, node_id: str, rtt_ms: float,
                       loss_percent: float) -> tuple:
        """更新评分（复用 QualityScorer 滑动窗口），返回 (score, grade)。"""
        scorer = self._scorers.setdefault(node_id, QualityScorer())
        score, grade = scorer.update(rtt_ms, loss_percent)
        self._scores[node_id] = (score, grade)
        self.metrics_updated.emit(node_id)
        self.node_updated.emit(node_id)
        return score, grade

    def get_score(self, node_id: str):
        """返回 (score, grade) 或 None。"""
        return self._scores.get(node_id)

    def get_scorer(self, node_id: str) -> QualityScorer | None:
        """直接访问评分器（供重置/调试）。"""
        return self._scorers.get(node_id)

    # ---------- 汇总 ----------

    def summary(self) -> dict:
        """聚合统计：总数/在线/离线/平均评分（供状态栏/批量视图）。"""
        statuses = self._statuses
        online = sum(1 for s in statuses.values() if s == "connected")
        offline = sum(1 for s in statuses.values()
                      if s in ("offline", "timeout", "auth_failed"))
        scores = [v[0] for v in self._scores.values()
                  if isinstance(v, tuple) and v and isinstance(v[0], (int, float))]
        avg = round(sum(scores) / len(scores), 1) if scores else None
        return {
            "total": self.count(),
            "online": online,
            "offline": offline,
            "avg_quality": avg,
        }
