# -*- coding: utf-8 -*-
"""
监控主机主窗口 —— 集中显示所有节点 + 本机节点（见《技术文档.md》§6）。

- 本机节点置顶，始终在线，RTT 0.00ms，不可移除。
- 远程节点多连接管理（NodeConnection + 独立重连）。
- 自适应三模式：单机/多机/概览。
- 按 node_id 路由信号更新对应列表/详情/概览。
- 节点管理：手动添加、自动扫描、右键菜单（移除/改别名/重连）。
- 状态记忆：窗口几何、节点列表、选中节点、视图模式。
- 顶部状态栏：已连接 N/M 节点。
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QMainWindow, QMessageBox,
                             QPushButton, QSplitter, QStackedWidget,
                             QVBoxLayout, QWidget)

from common.quality import QualityScorer
from common.utils import get_lan_ip, get_local_node_info, make_host_id
from host import config as host_config
from host.connection import NodeConnection
from node.discovery import DiscoveryListener
from host.gui.detail_panel import DetailPanel
from host.gui.discovery_dialog import DiscoveryDialog
from host.gui.node_list import LOCAL_NODE_ID, NodeListWidget
from host.gui.overview_grid import OverviewGrid
from host.local_node import LocalCollectorPack

log = logging.getLogger("host.gui.main_window")

MODE_AUTO = "auto"
MODE_OVERVIEW = "overview"


class HostMainWindow(QMainWindow):
    """监控主机主窗口。"""

    def __init__(self, cfg: dict = None):
        super().__init__()
        self.cfg = cfg or host_config.load_config()
        self.nodes = {}          # node_id → NodeConnection（远程）
        self.frames = {}         # node_id → 最近一帧
        self.statuses = {}       # node_id → 状态文本
        self.rtts = {}           # node_id → RTT ms
        self.losses = {}         # node_id → 丢包率
        self.scorers = {}        # node_id → QualityScorer
        self.scores = {}         # node_id → (score, grade)
        self.current_node = None
        self._view_mode = self.cfg.get("view_mode", MODE_AUTO)
        self.local_pack = None

        self._restore_geometry()
        self._build_ui()
        self._init_local_node()    # 本机节点置顶
        self._load_saved_nodes()   # 远程节点
        self._apply_view_mode()

        # UDP 心跳监听（自动发现）
        self.listener = DiscoveryListener(udp_port=self.cfg.get("udp_port", 12346))
        self.listener.start()
        log.info("监控主机主窗口已创建")

    # ---------- 几何与状态记忆 ----------

    def _restore_geometry(self) -> None:
        g = self.cfg.get("window_geometry", {})
        self.setGeometry(g.get("x", 100), g.get("y", 100),
                         g.get("w", 1400), g.get("h", 900))

    def _save_geometry(self) -> None:
        geo = self.geometry()
        self.cfg["window_geometry"] = {
            "x": geo.x(), "y": geo.y(), "w": geo.width(), "h": geo.height(),
        }
        host_config.save_config(self.cfg)

    def _save_state(self) -> None:
        self.cfg["last_selected_node"] = self.current_node or ""
        self.cfg["view_mode"] = self._view_mode
        self._save_geometry()

    # ---------- UI ----------

    def _build_ui(self) -> None:
        self.setWindowTitle("监控主机 — 集中监控")
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)

        # 顶部工具栏
        top = QHBoxLayout()
        self.top_label = QLabel("已连接 0/0 节点")
        self.top_label.setObjectName("panel_title")
        top.addWidget(self.top_label)
        top.addStretch(1)

        self.btn_overview = QPushButton("概览")
        self.btn_overview.setCheckable(True)
        self.btn_overview.clicked.connect(self._on_toggle_overview)
        top.addWidget(self.btn_overview)

        btn_add = QPushButton("添加节点")
        btn_add.clicked.connect(self._on_add_node)
        top.addWidget(btn_add)
        btn_scan = QPushButton("扫描")
        btn_scan.clicked.connect(self._on_scan_nodes)
        top.addWidget(btn_scan)
        root.addLayout(top)

        # 中部：详情页 与 概览页
        self.detail_stack = QStackedWidget()

        self.detail_page = QWidget()
        detail_layout = QHBoxLayout(self.detail_page)
        detail_layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Horizontal)

        # 左侧节点列表 + 删除按钮
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)
        self.node_list = NodeListWidget()
        self.node_list.currentItemChanged.connect(self._on_node_selected)
        self.node_list.context_action.connect(self._on_context_action)
        left_layout.addWidget(self.node_list, 1)
        # 显式删除按钮（替代仅右键菜单）
        self.btn_delete = QPushButton("删除选中节点")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        self.node_list.currentItemChanged.connect(self._on_delete_selection)
        left_layout.addWidget(self.btn_delete)
        self.splitter.addWidget(left_panel)

        self.detail_panel = DetailPanel()
        self.splitter.addWidget(self.detail_panel)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        detail_layout.addWidget(self.splitter)
        self.detail_stack.addWidget(self.detail_page)

        self.overview = OverviewGrid(
            max_cards_per_row=self.cfg.get("max_cards_per_row", 4))
        self.overview.set_card_limit(self.cfg.get("max_overview_cards", 16))
        self.overview.node_clicked.connect(self._on_overview_card_clicked)
        self.detail_stack.addWidget(self.overview)

        root.addWidget(self.detail_stack, stretch=1)

        # 底部状态栏
        self.statusBar().showMessage("就绪")
        self.setCentralWidget(central)

    # ---------- 本机节点 ----------

    def _init_local_node(self) -> None:
        """初始化本机节点：置顶列表、创建本地采集包。"""
        self.local_pack = LocalCollectorPack(self.cfg)
        self.local_pack.local_data.connect(self._on_data)
        self.local_pack.start()

        self.nodes[LOCAL_NODE_ID] = None   # 占位（无 NodeConnection）
        self.statuses[LOCAL_NODE_ID] = "在线"
        self.rtts[LOCAL_NODE_ID] = 0.0
        # 本机节点真实局域网 IP（而非硬编码 localhost）
        local_ip = get_lan_ip(self.cfg.get("preferred_iface", ""))
        # 列表置顶
        self.node_list.add_node(LOCAL_NODE_ID, "本机 (localhost)", local_ip,
                                is_local=True)
        self.overview.add_card(LOCAL_NODE_ID, "本机 (localhost)", local_ip,
                               is_local=True)
        log.info("本机节点已初始化（置顶，IP=%s）", local_ip)

    # ---------- 远程节点管理 ----------

    def _load_saved_nodes(self) -> None:
        saved = self.cfg.get("hosts", [])
        for h in saved:
            self._add_node(h["node_id"], h["ip"], h["port"],
                           h.get("token", ""), h.get("alias", ""))
        last = self.cfg.get("last_selected_node", "")
        if last and last in self.nodes:
            self.node_list.select_node(last)
            self.current_node = last
        elif saved:
            self.node_list.setCurrentRow(0)

    def _add_node(self, node_id: str, ip: str, port: int,
                  token: str, alias: str) -> None:
        if node_id in self.nodes:
            return
        conn = NodeConnection(node_id, ip, port, token, alias)
        conn.data_received.connect(self._on_data)
        conn.status_changed.connect(self._on_status)
        conn.rtt_updated.connect(self._on_rtt)
        conn.loss_updated.connect(self._on_loss)
        self.nodes[node_id] = conn
        self.statuses[node_id] = "连接中"
        self.scorers[node_id] = QualityScorer()

        self.node_list.add_node(node_id, alias, ip)
        self.overview.add_card(node_id, alias, ip)
        conn.start()
        self._refresh_top()

    def _remove_node(self, node_id: str) -> None:
        if node_id == LOCAL_NODE_ID:
            return  # 本机节点不可移除
        conn = self.nodes.pop(node_id, None)
        if conn:
            conn.stop()
        self.frames.pop(node_id, None)
        self.statuses.pop(node_id, None)
        self.rtts.pop(node_id, None)
        self.losses.pop(node_id, None)
        self.scorers.pop(node_id, None)
        self.scores.pop(node_id, None)
        self.node_list.remove_node(node_id)
        self.overview.remove_card(node_id)
        host_config.remove_host(self.cfg, node_id)
        if self.current_node == node_id:
            self.current_node = None
        self._apply_view_mode()
        self._refresh_top()

    # ---------- 视图模式 ----------

    def connected_nodes(self) -> list:
        """已连接节点（含本机）的 node_id 列表。"""
        result = [LOCAL_NODE_ID]  # 本机始终在线
        result += [nid for nid, conn in self.nodes.items()
                   if conn is not None and conn.is_connected()]
        return result

    def _apply_view_mode(self) -> None:
        if self._view_mode == MODE_OVERVIEW:
            self.detail_stack.setCurrentWidget(self.overview)
            self.btn_overview.setChecked(True)
            return
        self.btn_overview.setChecked(False)
        connected = self.connected_nodes()
        if len(connected) <= 1:
            self._switch_single_mode()
        else:
            self._switch_multi_mode()

    def _switch_single_mode(self) -> None:
        self.node_list.hide()
        self.detail_stack.setCurrentWidget(self.detail_page)
        if self.current_node not in self.connected_nodes():
            self.current_node = LOCAL_NODE_ID
            self.node_list.select_node(self.current_node)

    def _switch_multi_mode(self) -> None:
        self.node_list.show()
        self.detail_stack.setCurrentWidget(self.detail_page)

    def _on_toggle_overview(self) -> None:
        self._view_mode = MODE_OVERVIEW if self.btn_overview.isChecked() else MODE_AUTO
        self._apply_view_mode()

    def _on_overview_card_clicked(self, node_id: str) -> None:
        self._view_mode = MODE_AUTO
        self._apply_view_mode()
        self.current_node = node_id
        self.node_list.select_node(node_id)
        if node_id in self.frames:
            self.detail_panel.update_all(self.frames[node_id])

    # ---------- 添加/扫描/右键 ----------

    def _on_add_node(self) -> None:
        from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout,
                                     QLabel, QLineEdit)

        dialog = QDialog(self)
        dialog.setWindowTitle("手动添加节点")
        form = QFormLayout(dialog)

        # 提示：告诉用户各字段填什么
        hint = QLabel(
            "填被监控电脑（采集节点）的信息：\n"
            "· IP：该电脑的局域网 IP（如 192.168.1.100）\n"
            "· 端口：采集节点 TCP 端口，默认 12345\n"
            "· Token：采集节点 node_config.json 中的 token\n"
            "· 别名：任意名称，便于识别"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #808080;")
        form.addRow(hint)

        ip_edit = QLineEdit()
        port_edit = QLineEdit("12345")
        token_edit = QLineEdit()
        alias_edit = QLineEdit()
        form.addRow("IP *", ip_edit)
        form.addRow("端口", port_edit)
        form.addRow("Token *", token_edit)
        form.addRow("别名", alias_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec_() != QDialog.Accepted:
            return
        ip = ip_edit.text().strip()
        if not ip:
            self.statusBar().showMessage("IP 不能为空", 3000)
            return
        try:
            port = int(port_edit.text().strip() or "12345")
        except ValueError:
            port = 12345
        node_id = make_host_id(ip, port)
        if node_id in self.nodes:
            self.statusBar().showMessage("该节点已添加", 3000)
            return
        alias = alias_edit.text().strip() or f"{ip}:{port}"
        token = token_edit.text().strip()
        host_config.upsert_host(self.cfg, node_id, ip, port, token, alias)
        self._add_node(node_id, ip, port, token, alias)

    def _on_scan_nodes(self) -> None:
        existing = set(self.nodes.keys())
        dialog = DiscoveryDialog(self.listener, existing,
                                 on_add=self._on_discovery_add,
                                 on_add_local=self._on_add_local_node,
                                 parent=self)
        dialog.exec_()

    def _on_add_local_node(self) -> None:
        """一键接入本机采集节点（读取 node_config.json 自动填入）。"""
        info = get_local_node_info()
        if not info or not info.get("token"):
            QMessageBox.warning(
                self, "未找到本机节点",
                "未找到 node_config.json 或未配置 token。\n"
                "请先在被监控电脑上启动采集节点（python -m node）生成配置。")
            return
        node_id = make_host_id(info["ip"], info["port"])
        if node_id in self.nodes:
            self.statusBar().showMessage("本机节点已在列表中", 3000)
            return
        host_config.upsert_host(self.cfg, node_id, info["ip"], info["port"],
                                info["token"], info["alias"])
        self._add_node(node_id, info["ip"], info["port"],
                       info["token"], info["alias"])
        self.statusBar().showMessage(f"已接入本机节点 {info['ip']}", 3000)

    def _on_discovery_add(self, ip, port, token, alias) -> None:
        node_id = make_host_id(ip, port)
        host_config.upsert_host(self.cfg, node_id, ip, port, token, alias)
        self._add_node(node_id, ip, port, token, alias)

    def _on_context_action(self, action: str, node_id: str) -> None:
        if node_id == LOCAL_NODE_ID:
            return  # 本机节点不可操作
        if action == "remove":
            alias = self.nodes[node_id].alias if node_id in self.nodes else node_id
            reply = QMessageBox.question(
                self, "移除节点", f"确认移除节点「{alias}」？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self._remove_node(node_id)
        elif action == "edit_alias":
            self._edit_alias(node_id)
        elif action == "reconnect":
            conn = self.nodes.get(node_id)
            if conn:
                conn.stop()
                self._add_node(node_id, conn.ip, conn.port, conn.token, conn.alias)

    def _edit_alias(self, node_id: str) -> None:
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit

        conn = self.nodes.get(node_id)
        if conn is None:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑别名")
        form = QFormLayout(dialog)
        alias_edit = QLineEdit(conn.alias)
        form.addRow("别名:", alias_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec_() != QDialog.Accepted:
            return
        alias = alias_edit.text().strip() or conn.alias
        if alias == conn.alias:
            return
        conn.alias = alias
        host_config.upsert_host(self.cfg, conn.node_id, conn.ip, conn.port,
                                conn.token, alias)
        widget = self.node_list.get_widget(node_id)
        if widget:
            widget.alias_label.setText(alias)
        card = self.overview._cards.get(node_id)
        if card:
            card.alias = alias

    # ---------- 信号槽：按 node_id 分发 ----------

    def _on_node_selected(self, current, _previous) -> None:
        if current is None:
            self.current_node = None
            return
        self.current_node = current.data(Qt.UserRole)
        if self.current_node in self.frames:
            self.detail_panel.update_all(self.frames[self.current_node])

    def _on_delete_selection(self, current, _previous) -> None:
        """删除按钮可用性：选中远程节点可删，本机节点/无选中禁用。"""
        if current is None:
            self.btn_delete.setEnabled(False)
            return
        self.btn_delete.setEnabled(current.data(Qt.UserRole) != LOCAL_NODE_ID)

    def _on_delete_clicked(self) -> None:
        """删除按钮 → 复用右键删除流程。"""
        item = self.node_list.currentItem()
        if item is None:
            return
        node_id = item.data(Qt.UserRole)
        if node_id == LOCAL_NODE_ID:
            return
        self._on_context_action("remove", node_id)

    def _on_data(self, frame: dict, node_id: str) -> None:
        """接收 monitor_data：注入本地测量的网络质量 + 更新显示。"""
        self._inject_net_quality(frame, node_id)
        self.frames[node_id] = frame

        summary = self.detail_panel.get_summary(frame)
        self.overview.update_card(node_id, summary,
                                  self.statuses.get(node_id, ""))
        widget = self.node_list.get_widget(node_id)
        if widget:
            widget.update_summary(summary)

        if node_id == self.current_node:
            self.detail_panel.update_all(frame)

    def _inject_net_quality(self, frame: dict, node_id: str) -> None:
        """将本机测量的 RTT/丢包/评分注入帧的 net_quality（§18.5）。"""
        nq = frame.get("net_quality", {})
        if not isinstance(nq, dict):
            nq = {}
        if node_id == LOCAL_NODE_ID:
            nq["latency_to_client_ms"] = 0.0   # 本机 RTT 固定 0.00ms
            nq["quality_score"] = "N/A"
            frame["net_quality"] = nq
            return
        rtt = self.rtts.get(node_id)
        if rtt is not None:
            nq["latency_to_client_ms"] = round(rtt, 3)
        loss = self.losses.get(node_id)
        if loss is not None:
            nq["packet_loss_percent"] = loss
        scorer = self.scorers.get(node_id)
        if scorer is not None and rtt is not None and loss is not None:
            score, grade = scorer.update(rtt, loss)
            nq["quality_score"] = score
            nq["quality_grade"] = grade
            self.scores[node_id] = (score, grade)
        frame["net_quality"] = nq

    def _on_status(self, status: str, node_id: str) -> None:
        self.statuses[node_id] = status
        widget = self.node_list.get_widget(node_id)
        if widget:
            widget.update_status(status)
        summary = self.detail_panel.get_summary(self.frames.get(node_id, {}))
        self.overview.update_card(node_id, summary, status)
        self._refresh_top()
        self._apply_view_mode()
        self.statusBar().showMessage(f"{self.nodes[node_id].alias}: {status}", 3000)

    def _on_rtt(self, rtt_ms: float, node_id: str) -> None:
        self.rtts[node_id] = rtt_ms
        widget = self.node_list.get_widget(node_id)
        if widget:
            widget.update_rtt(rtt_ms)

    def _on_loss(self, loss: float, node_id: str) -> None:
        self.losses[node_id] = loss

    def _refresh_top(self) -> None:
        n = len(self.connected_nodes())
        self.top_label.setText(f"已连接 {n}/{len(self.nodes)} 节点")

    # ---------- 窗口事件 ----------

    def closeEvent(self, event) -> None:
        for conn in self.nodes.values():
            if conn:
                conn.stop()
        if self.local_pack:
            self.local_pack.stop()
        self.listener.stop()
        self._save_state()
        event.accept()
