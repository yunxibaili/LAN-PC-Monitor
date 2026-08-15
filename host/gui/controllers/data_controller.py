# -*- coding: utf-8 -*-
"""
DataController —— WS 数据入口 + 节点生命周期控制（v5.2 Phase 3-8）。

职责：
  - NodeConnection 信号 → Store（FrameStore/NodeStore/HistoryStore）
  - 节点添加/移除（含 Store 生命周期同步 + UI 列表/侧栏同步）
  - 后台自动发现
  - 评分注入（net_quality）

不直接创建 UI 组件；通过回调通知 MainWindow 更新页面。
"""
import logging

from common.utils import get_lan_ip, make_host_id
from common.constants import LOCAL_NODE_ID
from common.i18n import tr
from host import config as host_config
from host.service.discovery_service import DiscoveryService

log = logging.getLogger("host.gui.controllers.data")


class DataController:
    """WS 数据入口 + 节点生命周期控制器。"""

    def __init__(self, cfg: dict, frame_store, node_store, history_store,
                 discovery: DiscoveryService, persistence=None,
                 on_node_added=None, on_node_removed=None):
        """
        :param cfg:           host_config 字典
        :param frame_store:   FrameStore
        :param node_store:    NodeStore
        :param history_store: HistoryStore
        :param discovery:     DiscoveryService
        :param persistence:   可选 MetricPersistenceService（持久化到 SQLite）
        :param on_node_added:   回调(node_id, conn) —— 页面同步
        :param on_node_removed: 回调(node_id) —— 页面同步
        """
        self.cfg = cfg
        self.frame_store = frame_store
        self.node_store = node_store
        self.history_store = history_store
        self.discovery = discovery
        self.persistence = persistence
        self.on_node_added = on_node_added
        self.on_node_removed = on_node_removed
        self.nodes = {}          # node_id → NodeConnection
        self.current_node = None
        self._on_data_cb = None  # 每帧回调（告警/页面更新）
        self._on_status_cb = None
        self._on_rtt_cb = None
        self._on_loss_cb = None

    # ---------- 数据回调注册 ----------

    def set_callbacks(self, on_data=None, on_status=None,
                      on_rtt=None, on_loss=None) -> None:
        self._on_data_cb = on_data
        self._on_status_cb = on_status
        self._on_rtt_cb = on_rtt
        self._on_loss_cb = on_loss

    # ---------- 节点生命周期 ----------

    def add_node(self, node_id: str, ip: str, port: int,
                 token: str, alias: str) -> None:
        """创建 NodeConnection 并连接。"""
        if node_id in self.nodes:
            return
        from host.facade.connection_factory import create_connection
        conn = create_connection(node_id, ip, port, token, alias)
        conn.data_received.connect(self._on_data)
        conn.status_changed.connect(self._on_status)
        conn.rtt_updated.connect(self._on_rtt)
        conn.loss_updated.connect(self._on_loss)
        self.nodes[node_id] = conn
        self.node_store.add_node(node_id, alias=alias, ip=ip, port=port)
        self.node_store.update_status(node_id, tr("node.connecting"))
        conn.start()
        if self.on_node_added:
            self.on_node_added(node_id, conn)

    def remove_node(self, node_id: str) -> None:
        """移除节点并清理 Store。"""
        if node_id == LOCAL_NODE_ID:
            return  # 本机不可移除
        conn = self.nodes.pop(node_id, None)
        if conn:
            conn.stop()
        self.node_store.remove_node(node_id)
        self.frame_store.remove_node(node_id)
        self.history_store.remove_node(node_id)
        if self.current_node == node_id:
            self.current_node = None
        if self.on_node_removed:
            self.on_node_removed(node_id)

    def connected_node_ids(self) -> list:
        """已连接节点（含本机）node_id 列表。"""
        result = [LOCAL_NODE_ID]
        result += [nid for nid, conn in self.nodes.items()
                   if conn is not None and conn.is_connected()]
        return result

    # ---------- 本机节点 ----------

    def init_local_node(self, alias: str = "") -> None:
        """注册本机节点到 NodeStore（由 MainWindow 创建 LocalCollectorPack）。"""
        self.nodes[LOCAL_NODE_ID] = None
        self.node_store.add_node(LOCAL_NODE_ID, alias=alias or tr("node.local_alias"))
        self.node_store.update_status(LOCAL_NODE_ID, tr("node.online"))
        self.node_store.update_rtt(LOCAL_NODE_ID, 0.0)

    def load_saved_nodes(self) -> None:
        """从配置加载已保存节点并连接。"""
        for h in self.cfg.get("hosts", []):
            self.add_node(h["node_id"], h["ip"], h["port"],
                          h.get("token", ""), h.get("alias", ""))

    # ---------- 后台发现 ----------

    def auto_discover(self) -> None:
        """后台自动发现并接入节点。"""
        def _on_found(found: dict) -> None:
            for ip, info in found.items():
                try:
                    port = info.get("http_port") or info.get("port") or 12345
                    token = info.get("token", "")
                    node_id = make_host_id(ip, port)
                    if node_id in self.nodes:
                        continue
                    if self.cfg.get("auto_connect", True):
                        host_config.upsert_host(self.cfg, node_id, ip, port,
                                                token, info.get("alias", ""))
                        self.add_node(node_id, ip, port, token,
                                      info.get("alias", ""))
                except Exception:
                    continue
            log.info("后台自动发现完成，共发现 %d 个节点", len(found))

        self.discovery.auto_discover_background(on_found=_on_found)

    # ---------- WS 数据入口 ----------

    def _on_data(self, frame: dict, node_id: str) -> None:
        """monitor_data → Store + 持久化 + 回调。"""
        self._inject_net_quality(frame, node_id)
        self.frame_store.push(node_id, frame)
        self.history_store.push_frame(node_id, frame)
        if self.persistence is not None:
            self.persistence.persist_frame(node_id, frame)
        if self._on_data_cb:
            self._on_data_cb(frame, node_id)

    def _inject_net_quality(self, frame: dict, node_id: str) -> None:
        """注入本机测量的 RTT/丢包/评分。"""
        nq = frame.get("net_quality", {})
        if not isinstance(nq, dict):
            nq = {}
        if node_id == LOCAL_NODE_ID:
            nq["latency_to_client_ms"] = 0.0
            nq["quality_score"] = "N/A"
            frame["net_quality"] = nq
            return
        rtt = self.node_store.get_rtt(node_id)
        if rtt is not None:
            nq["latency_to_client_ms"] = round(rtt, 3)
        loss = self.node_store.get_loss(node_id)
        if loss is not None:
            nq["packet_loss_percent"] = loss
        scorer = self.node_store.get_scorer(node_id)
        if scorer is not None and rtt is not None and loss is not None:
            score, grade = self.node_store.update_quality(node_id, rtt, loss)
            nq["quality_score"] = score
            nq["quality_grade"] = grade
        frame["net_quality"] = nq

    def _on_status(self, status: str, node_id: str) -> None:
        self.node_store.update_status(node_id, status)
        if self._on_status_cb:
            self._on_status_cb(status, node_id)

    def _on_rtt(self, rtt_ms: float, node_id: str) -> None:
        self.node_store.update_rtt(node_id, rtt_ms)
        if self._on_rtt_cb:
            self._on_rtt_cb(rtt_ms, node_id)

    def _on_loss(self, loss: float, node_id: str) -> None:
        self.node_store.update_loss(node_id, loss)
        if self._on_loss_cb:
            self._on_loss_cb(loss, node_id)
