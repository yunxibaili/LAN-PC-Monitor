# -*- coding: utf-8 -*-
"""
监控主机主窗口 —— 集中显示所有节点 + 本机节点（见《README.md》§6）。

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
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QMainWindow, QMessageBox,
                             QPushButton, QSplitter, QStackedWidget,
                             QSystemTrayIcon, QVBoxLayout, QWidget)

from common.i18n import tr
from common.quality import QualityScorer
from common.utils import get_lan_ip, get_local_node_info, make_host_id
from host import config as host_config
from host.alerts import AlertEngine
from host.connection import NodeConnection
from node.discovery import DiscoveryListener, MdnsDiscovery
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

        # 红线告警引擎（第四篇）
        self.alert_engine = AlertEngine(host_config.load_alerts(self.cfg))
        self._alert_state = {}   # (node_id, path) → "red"/"warn" 上一状态（弹窗去重）
        self._tray = None

        self._restore_geometry()
        self._build_ui()
        self._init_tray()          # 系统托盘（告警气泡）
        self._init_local_node()    # 本机节点置顶
        self._load_saved_nodes()   # 远程节点
        self._apply_view_mode()

        # 节点发现：UDP 广播心跳 + mDNS 零配置，并行互为备份（§2.5.1）
        self.listener = DiscoveryListener(udp_port=self.cfg.get("udp_port", 12346))
        self.listener.start()
        self.mdns = MdnsDiscovery()
        self.mdns.start()
        log.info("监控主机主窗口已创建")

        # 首屏引导（§23.5）：首次运行弹出，一键接入发现的节点
        self._maybe_show_onboarding()

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
        self.setWindowTitle(tr("app.title.host"))
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)

        # 顶部工具栏
        top = QHBoxLayout()
        self.top_label = QLabel(tr("topbar.connected", 0, 0))
        self.top_label.setObjectName("panel_title")
        top.addWidget(self.top_label)
        top.addStretch(1)

        self.btn_overview = QPushButton(tr("topbar.overview"))
        self.btn_overview.setCheckable(True)
        self.btn_overview.clicked.connect(self._on_toggle_overview)
        top.addWidget(self.btn_overview)

        btn_add = QPushButton(tr("topbar.add_node"))
        btn_add.clicked.connect(self._on_add_node)
        top.addWidget(btn_add)
        btn_scan = QPushButton(tr("topbar.scan"))
        btn_scan.clicked.connect(self._on_scan_nodes)
        top.addWidget(btn_scan)
        # 便捷连接入口（§2.5）：连接码 / 剪贴板 / 导入 / 导出
        btn_code = QPushButton(tr("topbar.connect_code"))
        btn_code.setToolTip(tr("node_mgr.tip_conn_code"))
        btn_code.clicked.connect(self._on_connect_code)
        top.addWidget(btn_code)
        btn_clip = QPushButton(tr("topbar.clipboard"))
        btn_clip.setToolTip(tr("node_mgr.tip_clipboard"))
        btn_clip.clicked.connect(self._on_clipboard)
        top.addWidget(btn_clip)
        btn_imp = QPushButton(tr("topbar.import"))
        btn_imp.setToolTip(tr("node_mgr.tip_import"))
        btn_imp.clicked.connect(self._on_import)
        top.addWidget(btn_imp)
        btn_exp = QPushButton(tr("topbar.export"))
        btn_exp.setToolTip(tr("node_mgr.tip_export"))
        btn_exp.clicked.connect(self._on_export)
        top.addWidget(btn_exp)
        root.addLayout(top)

        # 中部：详情页 与 概览页
        self.detail_stack = QStackedWidget()

        self.detail_page = QWidget()
        detail_layout = QHBoxLayout(self.detail_page)
        detail_layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Horizontal)

        # 左侧节点列表（删除仅通过右键菜单，§7.1）
        self.node_list = NodeListWidget()
        self.node_list.currentItemChanged.connect(self._on_node_selected)
        self.node_list.context_action.connect(self._on_context_action)
        self.splitter.addWidget(self.node_list)

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
        self.statusBar().showMessage(tr("topbar.ready"))
        self.setCentralWidget(central)

    # ---------- 本机节点 ----------

    def _init_local_node(self) -> None:
        """初始化本机节点：置顶列表、创建本地采集包。"""
        self.local_pack = LocalCollectorPack(self.cfg)
        self.local_pack.local_data.connect(self._on_data)
        self.local_pack.start()

        self.nodes[LOCAL_NODE_ID] = None   # 占位（无 NodeConnection）
        self.statuses[LOCAL_NODE_ID] = tr("node.online")
        self.rtts[LOCAL_NODE_ID] = 0.0
        # 本机节点真实局域网 IP（而非硬编码 localhost）
        local_ip = get_lan_ip(self.cfg.get("preferred_iface", ""))
        # 列表置顶
        self.node_list.add_node(LOCAL_NODE_ID, tr("node.local_alias"), local_ip,
                                is_local=True)
        self.overview.add_card(LOCAL_NODE_ID, tr("node.local_alias"), local_ip,
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
        self.statuses[node_id] = tr("node.connecting")
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
        dialog.setWindowTitle(tr("dialog.add_node"))
        from common.theme import remove_help_button
        remove_help_button(dialog)   # 移除 Windows 标题栏问号按钮，防闪退
        form = QFormLayout(dialog)

        # 提示：告诉用户各字段填什么
        hint = QLabel(tr("dialog.add_node_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {theme.COLOR_NA};")
        form.addRow(hint)

        ip_edit = QLineEdit()
        port_edit = QLineEdit("12345")
        token_edit = QLineEdit()
        alias_edit = QLineEdit()
        form.addRow("IP *", ip_edit)
        form.addRow(tr("dialog.port"), port_edit)
        form.addRow("Token *", token_edit)
        form.addRow(tr("dialog.alias"), alias_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec_() != QDialog.Accepted:
            return
        ip = ip_edit.text().strip()
        if not ip:
            self.statusBar().showMessage(tr("dialog.ip_empty"), 3000)
            return
        try:
            port = int(port_edit.text().strip() or "12345")
        except ValueError:
            port = 12345
        node_id = make_host_id(ip, port)
        if node_id in self.nodes:
            self.statusBar().showMessage(tr("dialog.already_added"), 3000)
            return
        alias = alias_edit.text().strip() or f"{ip}:{port}"
        token = token_edit.text().strip()
        host_config.upsert_host(self.cfg, node_id, ip, port, token, alias)
        self._add_node(node_id, ip, port, token, alias)

    def _on_scan_nodes(self) -> None:
        existing = set(self.nodes.keys())
        dialog = DiscoveryDialog(self.merged_hosts, existing,
                                 on_add=self._on_discovery_add,
                                 on_add_local=self._on_add_local_node,
                                 parent=self)
        dialog.exec_()

    def _on_connect_code(self) -> None:
        """连接码接入（§23.2）。"""
        from common.connect_dialog import ConnectCodeDialog
        dialog = ConnectCodeDialog(self.merged_hosts,
                                   on_add=self._on_discovery_add, parent=self)
        dialog.exec_()

    def _on_clipboard(self) -> None:
        """从剪贴板连接串添加（§23.3）。"""
        from common.connect_dialog import ClipboardDialog
        dialog = ClipboardDialog(on_add=self._on_discovery_add, parent=self)
        dialog.exec_()

    def _on_import(self) -> None:
        """导入 .pcm 配置文件（§23.4）。"""
        from PyQt5.QtWidgets import QFileDialog
        from common.connect_code import import_config
        path, _ = QFileDialog.getOpenFileName(
            self, tr("connect.import_title"), "", tr("connect.import_filter"))
        if not path:
            return
        nodes = import_config(path)
        if nodes is None:
            QMessageBox.warning(self, tr("connect.import_fail"), tr("connect.import_fail_msg"))
            return
        for n in nodes:
            node_id = make_host_id(n["ip"], n["port"])
            host_config.upsert_host(self.cfg, node_id, n["ip"], n["port"],
                                    n["token"], n["alias"])
            self._add_node(node_id, n["ip"], n["port"], n["token"], n["alias"])
        self.statusBar().showMessage(tr("connect.imported", len(nodes)), 3000)

    def _on_export(self) -> None:
        """导出当前节点列表为 .pcm 配置（§23.4）。"""
        from PyQt5.QtWidgets import QFileDialog
        from common.connect_code import export_config
        nodes = list(self.cfg.get("hosts", []))
        path, _ = QFileDialog.getSaveFileName(
            self, tr("connect.export_title"), "pcmonitor_nodes.pcm", tr("connect.export_filter"))
        if not path:
            return
        ok = export_config(nodes, path)
        self.statusBar().showMessage(
            tr("connect.export_ok") if ok else tr("connect.export_fail"), 3000)

    def _maybe_show_onboarding(self) -> None:
        """首屏引导（§23.5）：仅首次运行（无 onboarded 标记）弹出。"""
        if self.cfg.get("onboarded"):
            return
        from common.connect_dialog import OnboardingDialog
        from common.utils import get_lan_ip
        local_ip = get_lan_ip(self.cfg.get("preferred_iface", ""))
        dialog = OnboardingDialog(
            self.merged_hosts, local_ip=local_ip,
            on_add_all=self._on_discovery_add, parent=self)
        dialog.exec_()
        self.cfg["onboarded"] = True
        host_config.save_config(self.cfg)

    @property
    def merged_hosts(self):
        """合并 UDP 广播 + mDNS 发现的节点（按 ip 去重，mDNS 优先保留）。"""
        hosts = dict(self.listener.get_hosts())
        for ip, info in self.mdns.get_hosts().items():
            if ip in hosts:
                hosts[ip].update(info)
            else:
                hosts[ip] = info
        return hosts

    def _on_add_local_node(self) -> None:
        """一键接入本机采集节点（读取 node_config.json 自动填入）。"""
        info = get_local_node_info()
        if not info or not info.get("token"):
            QMessageBox.warning(
                self, tr("local_node.not_found"),
                tr("local_node.not_found_msg"))
            return
        node_id = make_host_id(info["ip"], info["port"])
        if node_id in self.nodes:
            self.statusBar().showMessage(tr("local_node.already"), 3000)
            return
        host_config.upsert_host(self.cfg, node_id, info["ip"], info["port"],
                                info["token"], info["alias"])
        self._add_node(node_id, info["ip"], info["port"],
                       info["token"], info["alias"])
        self.statusBar().showMessage(tr("local_node.added", info["ip"]), 3000)

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
                self, tr("dialog.remove_node"), tr("dialog.confirm_remove", alias),
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
        dialog.setWindowTitle(tr("dialog.edit_alias"))
        from common.theme import remove_help_button
        remove_help_button(dialog)   # 移除 Windows 标题栏问号按钮，防闪退
        form = QFormLayout(dialog)
        alias_edit = QLineEdit(conn.alias)
        form.addRow(tr("dialog.alias_label"), alias_edit)
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

    def _on_data(self, frame: dict, node_id: str) -> None:
        """接收 monitor_data：注入本地测量的网络质量 + 更新显示 + 红线告警。"""
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

        # 红线告警检测（第四篇）
        self._check_alerts(frame, node_id)

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

    # ---------- 红线告警（第四篇） ----------

    def _init_tray(self) -> None:
        """初始化系统托盘图标（告警气泡）。不可用时静默降级。"""
        try:
            if not QSystemTrayIcon.isSystemTrayAvailable():
                return
            self._tray = QSystemTrayIcon(self)
            # 无图标时用一个纯色 QPixmap 占位
            pix = QIcon().pixmap(16, 16)
            if pix.isNull():
                from PyQt5.QtGui import QPixmap, QColor
                pm = QPixmap(16, 16)
                pm.fill(QColor("#007acc"))
                self._tray.setIcon(QIcon(pm))
            else:
                self._tray.setIcon(QIcon(pix))
            self._tray.setToolTip(tr("app.title.host"))
            self._tray.show()
        except Exception as e:
            log.debug("系统托盘初始化失败（告警弹窗降级为状态栏+日志）: %s", e)
            self._tray = None

    def _check_alerts(self, frame: dict, node_id: str) -> None:
        """
        检测红线告警：状态栏 + 日志 + 托盘气泡（red 去重弹窗）。
        """
        alerts = self.alert_engine.check(frame)
        if not alerts:
            # 无告警 → 清空本节点告警，状态栏恢复
            self._clear_node_alerts(node_id)
            return

        red = [a for a in alerts if a["level"] == "red"]
        warn = [a for a in alerts if a["level"] == "warn"]

        # 状态栏
        self._update_status_bar(red, warn)

        # 日志 + 托盘（red 去重）
        for a in red:
            key = (node_id, a["path"])
            if self._alert_state.get(key) != "red":
                self._alert_state[key] = "red"
                log.warning("[alert] %s %s=%s 超红线 %s",
                            a["name"], a["path"], a["value"], a["threshold"])
                self._show_tray_alert(a)
        for a in warn:
            key = (node_id, a["path"])
            if self._alert_state.get(key) != "warn":
                self._alert_state[key] = "warn"
                log.info("[alert] %s %s=%s 达预警 %s",
                         a["name"], a["path"], a["value"], a["threshold"])

    def _clear_node_alerts(self, node_id: str) -> None:
        """节点恢复正常 → 清除其告警状态，刷新状态栏。"""
        changed = False
        for key in list(self._alert_state.keys()):
            if key[0] == node_id:
                del self._alert_state[key]
                changed = True
        if changed:
            self.statusBar().showMessage(tr("topbar.ready"), 3000)

    def _update_status_bar(self, red: list, warn: list) -> None:
        """状态栏显示告警摘要。"""
        if red:
            text = tr("alert.red_summary", red[0]["name"], red[0]["value"])
            self.statusBar().setStyleSheet(
                f"color: #f44747; font-weight: bold;")
            self.statusBar().showMessage(text)
        elif warn:
            text = tr("alert.warn_summary", warn[0]["name"], warn[0]["value"])
            self.statusBar().setStyleSheet(
                f"color: #d7ba7d; font-weight: bold;")
            self.statusBar().showMessage(text)

    def _show_tray_alert(self, alert: dict) -> None:
        """托盘气泡告警（red 首次触发时调用）。"""
        if self._tray is None:
            return
        if not self.cfg.get("alert_popup", True):
            return
        try:
            self._tray.showMessage(
                tr("alert.tray_title"),
                tr("alert.tray_body", alert["name"], alert["value"],
                   alert["threshold"]),
                QSystemTrayIcon.Warning, 5000)
        except Exception as e:
            log.debug("托盘气泡显示失败: %s", e)

    def _refresh_top(self) -> None:
        n = len(self.connected_nodes())
        self.top_label.setText(tr("topbar.connected", n, len(self.nodes)))

    # ---------- 窗口事件 ----------

    def closeEvent(self, event) -> None:
        for conn in self.nodes.values():
            if conn:
                conn.stop()
        if self.local_pack:
            self.local_pack.stop()
        self.listener.stop()
        self.mdns.stop()
        if self._tray:
            try:
                self._tray.hide()
            except Exception:
                pass
        self._save_state()
        event.accept()
