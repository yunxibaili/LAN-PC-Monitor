# -*- coding: utf-8 -*-
"""
DashboardViewModel —— Dashboard 页面数据转换层（v5.2 Phase 3-2A）。

职责：
  - 监听 NodeStore / FrameStore 信号
  - 将 monitor_data 帧转换为 DashboardNodeData（UI 可直接渲染的扁平结构）
  - 不直接访问 MainWindow.frames / MainWindow.nodes
  - 不处理 monitor_data 协议细节

数据流：
  NodeStore.node_added    -> 生成空 DashboardNodeData
  FrameStore.frame_updated -> 填充 DashboardNodeData 的指标字段
  NodeStore.status_changed -> 更新 DashboardNodeData 的状态
  NodeStore.metrics_updated -> 更新 DashboardNodeData 的评分

输出：
  DashboardNodeData — 扁平数据结构，供 NodeCard 组件消费
"""
import logging

from host.store.signals import Signal

log = logging.getLogger("host.viewmodels.dashboard_vm")


class DashboardNodeData:
    """Dashboard 卡片数据（扁平，UI 可直接渲染）。"""

    __slots__ = (
        "node_id", "alias", "status",
        "cpu_usage", "gpu_usage", "memory_usage",
        "network_rx", "network_tx",
        "quality_score", "quality_grade",
    )

    def __init__(self, node_id: str = "", alias: str = ""):
        self.node_id = node_id
        self.alias = alias
        self.status = "connecting"
        self.cpu_usage = 0.0
        self.gpu_usage = 0.0
        self.memory_usage = 0.0
        self.network_rx = 0.0
        self.network_tx = 0.0
        self.quality_score = 0
        self.quality_grade = ""

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "alias": self.alias,
            "status": self.status,
            "cpu_usage": self.cpu_usage,
            "gpu_usage": self.gpu_usage,
            "memory_usage": self.memory_usage,
            "network_rx": self.network_rx,
            "network_tx": self.network_tx,
            "quality_score": self.quality_score,
            "quality_grade": self.quality_grade,
        }


class DashboardViewModel:
    """
    Dashboard 数据转换层。

    监听 NodeStore + FrameStore 信号，维护 DashboardNodeData 列表。
    页面通过 get_nodes() / get_node() 读取数据。
    """

    nodes_changed = Signal()  # 节点列表变化（增删）
    data_changed = Signal(str)  # 某节点数据更新（node_id）

    def __init__(self, node_store, frame_store):
        """
        :param node_store: NodeStore 实例
        :param frame_store: FrameStore 实例
        """
        self._node_store = node_store
        self._frame_store = frame_store
        self._nodes = {}  # node_id -> DashboardNodeData

        # 监听 NodeStore 信号
        self._node_store.node_added.connect(self._on_node_added)
        self._node_store.node_removed.connect(self._on_node_removed)
        self._node_store.status_changed.connect(self._on_status_changed)
        self._node_store.metrics_updated.connect(self._on_metrics_updated)

        # 监听 FrameStore 信号
        self._frame_store.frame_updated.connect(self._on_frame_updated)

    # ---------- 信号处理 ----------

    def _on_node_added(self, node_id: str) -> None:
        """节点加入时，创建空 DashboardNodeData。"""
        if node_id in self._nodes:
            return
        alias = self._node_store.get_alias(node_id)
        data = DashboardNodeData(node_id=node_id, alias=alias)
        data.status = self._node_store.get_status(node_id) or "connecting"
        self._nodes[node_id] = data
        self.nodes_changed.emit()
        log.debug("节点加入: %s (%s)", node_id, alias)

    def _on_node_removed(self, node_id: str) -> None:
        """节点移除时，清理 DashboardNodeData。"""
        if node_id in self._nodes:
            del self._nodes[node_id]
            self.nodes_changed.emit()
            log.debug("节点移除: %s", node_id)

    def _on_status_changed(self, node_id: str, status: str) -> None:
        """状态变更时，更新 DashboardNodeData。"""
        data = self._nodes.get(node_id)
        if data:
            data.status = status
            self.data_changed.emit(node_id)

    def _on_metrics_updated(self, node_id: str) -> None:
        """RTT/丢包/评分更新时，刷新 DashboardNodeData。"""
        data = self._nodes.get(node_id)
        if not data:
            return
        score_info = self._node_store.get_score(node_id)
        if score_info:
            data.quality_score = score_info[0]
            data.quality_grade = score_info[1]
        self.data_changed.emit(node_id)

    def _on_frame_updated(self, node_id: str, frame: dict) -> None:
        """帧更新时，从 monitor_data 提取指标填充 DashboardNodeData。"""
        data = self._nodes.get(node_id)
        if not data:
            return
        # 从帧中提取 Dashboard 所需的 6 项指标
        cpu = frame.get("cpu", {})
        gpu = frame.get("gpu", {})
        ram = frame.get("ram", {})
        net = frame.get("net", {})
        data.cpu_usage = _safe_float(cpu.get("total_usage"))
        data.gpu_usage = _safe_float(gpu.get("usage_percent"))
        data.memory_usage = _safe_float(ram.get("usage_percent"))
        data.network_rx = _safe_float(net.get("download_mb_s"))
        data.network_tx = _safe_float(net.get("upload_mb_s"))
        self.data_changed.emit(node_id)

    # ---------- 查询接口 ----------

    def get_nodes(self) -> list:
        """返回所有 DashboardNodeData（列表副本）。"""
        return list(self._nodes.values())

    def get_node(self, node_id: str):
        """返回单个 DashboardNodeData；不存在返回 None。"""
        return self._nodes.get(node_id)

    def node_ids(self) -> list:
        return list(self._nodes.keys())

    def count(self) -> int:
        return len(self._nodes)


def _safe_float(val, default=0.0) -> float:
    """安全转换为 float；N/A/None/无效值返回 default。"""
    if val is None or val == "N/A":
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default
