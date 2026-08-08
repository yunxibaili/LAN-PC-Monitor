# -*- coding: utf-8 -*-
"""
副机端主窗口 —— 本机仪表盘 + 节点管理器（见《技术文档.md》§6 / §20.8）。

布局：
    ┌─────────────────────────────┬─────────────────────────┐
    │ 本机仪表盘（主视图，固定）     │ 节点管理器（侧栏，摘要）   │
    │ CPU/GPU/内存/磁盘/网络/帧率  │ 已接入节点列表            │
    │ /进程 分区 + 变色             │ 添加/扫描按钮             │
    │ 顶部：主机名/IP/uptime/本机   │ 本机节点置顶[本机]        │
    │ 底部：已接入远程节点数         │                         │
    └─────────────────────────────┴─────────────────────────┘

- 本机数据经 LocalCollectorPack 直供（不经网络）。
- 远程节点仅维护摘要（状态/RTT/评分），点击不展开详情。
- 关闭窗口弹确认"确定退出副机端监控"；最小化/隐藏时后台连接继续。
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QMainWindow, QMessageBox,
                             QSplitter, QVBoxLayout, QWidget)

from common.quality import QualityScorer
from common.utils import get_lan_ip, get_local_node_info, make_host_id
from client import config as client_config
from client.connection import NodeConnection
from client.discovery import DiscoveryListener, MdnsDiscovery
from client.gui.discovery_dialog import DiscoveryDialog
from client.gui.local_panel import LocalPanel
from client.gui.node_manager import NodeManager
from client.local_node import LOCAL_NODE_ID, LocalCollectorPack

log = logging.getLogger("client.gui.main_window")


class ClientMainWindow(QMainWindow):
    """副机端主窗口。"""

    def __init__(self, cfg: dict = None):
        super().__init__()
        self.cfg = cfg or client_config.load_config()
        self.nodes = {}          # node_id → NodeConnection（远程）
        self.statuses = {}       # node_id → 状态文本
        self.rtts = {}           # node_id → RTT ms
        self.losses = {}         # node_id → 丢包率
        self.scorers = {}        # node_id → QualityScorer
        self.local_pack = None

        self._restore_geometry()
        self._build_ui()
        self._init_local_node()    # 本机节点置顶
        self._load_saved_nodes()   # 远程节点

        # 节点发现：UDP 广播心跳 + mDNS 零配置，并行互为备份（§2.5.1）
        self.listener = DiscoveryListener(udp_port=self.cfg.get("udp_port", 12346))
        self.listener.start()
        self.mdns = MdnsDiscovery()
        self.mdns.start()
        log.info("副机端主窗口已创建")

        # 首屏引导（§23.5）：首次运行弹出，一键接入发现的节点
        self._maybe_show_onboarding()

    # ---------- 几何 ----------

    def _restore_geometry(self) -> None:
        g = self.cfg.get("window_geometry", {})
        self.setGeometry(g.get("x", 100), g.get("y", 100),
                         g.get("w", 1000), g.get("h", 700))

    def _save_geometry(self) -> None:
        geo = self.geometry()
        self.cfg["window_geometry"] = {
            "x": geo.x(), "y": geo.y(), "w": geo.width(), "h": geo.height(),
        }
        client_config.save_config(self.cfg)

    # ---------- UI ----------

    def _build_ui(self) -> None:
        self.setWindowTitle("副机端 — 本机仪表盘")
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)

        # 顶部：已接入远程节点数
        top = QHBoxLayout()
        self.top_label = QLabel("已接入远程节点: 0")
        self.top_label.setObjectName("panel_title")
        top.addWidget(self.top_label)
        top.addStretch(1)
        root.addLayout(top)

        # 中部：本机仪表盘（左，主视图） + 节点管理器（右，侧栏）
        self.splitter = QSplitter(Qt.Horizontal)
        self.local_panel = LocalPanel()
        self.splitter.addWidget(self.local_panel)

        self.node_manager = NodeManager()
        self.node_manager.add_clicked.connect(self._on_add_node)
        self.node_manager.add_local_clicked.connect(self._on_add_local_node)
        self.node_manager.scan_clicked.connect(self._on_scan_nodes)
        self.node_manager.connect_code_clicked.connect(self._on_connect_code)
        self.node_manager.clipboard_clicked.connect(self._on_clipboard)
        self.node_manager.import_clicked.connect(self._on_import)
        self.node_manager.export_clicked.connect(self._on_export)
        self.node_manager.context_action.connect(self._on_context_action)
        self.splitter.addWidget(self.node_manager)

        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        root.addWidget(self.splitter, 1)

        # 底部：提示
        self.statusBar().showMessage("就绪")
        self.setCentralWidget(central)

    # ---------- 本机节点 ----------

    def _init_local_node(self) -> None:
        """初始化本机节点：置顶列表 + 本地采集包。"""
        self.local_pack = LocalCollectorPack(self.cfg)
        self.local_pack.local_data.connect(self._on_local_data)
        self.local_pack.start()

        self.statuses[LOCAL_NODE_ID] = "在线"
        self.rtts[LOCAL_NODE_ID] = 0.0
        # 本机节点真实局域网 IP（而非硬编码 localhost）
        local_ip = get_lan_ip(self.cfg.get("preferred_iface", ""))
        self.node_manager.add_node(LOCAL_NODE_ID, "本机 (localhost)",
                                   local_ip, is_local=True)
        log.info("本机节点已初始化（置顶 [本机]，IP=%s）", local_ip)

    # ---------- 远程节点管理 ----------

    def _load_saved_nodes(self) -> None:
        saved = self.cfg.get("nodes", [])
        for n in saved:
            self._add_node(n["node_id"], n["ip"], n["port"],
                           n.get("token", ""), n.get("alias", ""))

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

        self.node_manager.add_node(node_id, alias, ip)
        self.node_manager.set_tooltip(node_id)   # "请在主机端查看"
        conn.start()
        self._refresh_top()

    def _remove_node(self, node_id: str) -> None:
        if node_id == LOCAL_NODE_ID:
            return
        conn = self.nodes.pop(node_id, None)
        if conn:
            conn.stop()
        self.statuses.pop(node_id, None)
        self.rtts.pop(node_id, None)
        self.losses.pop(node_id, None)
        self.scorers.pop(node_id, None)
        self.node_manager.remove_node(node_id)
        client_config.remove_node(self.cfg, node_id)
        self._refresh_top()

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
        client_config.upsert_node(self.cfg, node_id, ip, port, token, alias)
        self._add_node(node_id, ip, port, token, alias)

    def _on_scan_nodes(self) -> None:
        existing = set(self.nodes.keys())
        dialog = DiscoveryDialog(self.merged_hosts, existing,
                                 on_add=self._on_discovery_add,
                                 on_add_local=self._on_add_local_node,
                                 parent=self)
        dialog.exec_()

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
        # 记录已引导
        self.cfg["onboarded"] = True
        client_config.save_config(self.cfg)

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
                self, "未找到本机节点",
                "未找到 node_config.json 或未配置 token。\n"
                "请先在被监控电脑上启动采集节点（python -m node）生成配置。")
            return
        node_id = make_host_id(info["ip"], info["port"])
        if node_id in self.nodes:
            self.statusBar().showMessage("本机节点已在列表中", 3000)
            return
        client_config.upsert_node(self.cfg, node_id, info["ip"], info["port"],
                                  info["token"], info["alias"])
        self._add_node(node_id, info["ip"], info["port"],
                       info["token"], info["alias"])
        self.statusBar().showMessage(f"已接入本机节点 {info['ip']}", 3000)

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
            self, "导入节点配置", "", "监控配置 (*.pcm);;所有文件 (*)")
        if not path:
            return
        nodes = import_config(path)
        if nodes is None:
            QMessageBox.warning(self, "导入失败", "配置文件格式不正确")
            return
        for n in nodes:
            node_id = make_host_id(n["ip"], n["port"])
            client_config.upsert_node(self.cfg, node_id, n["ip"], n["port"],
                                      n["token"], n["alias"])
            self._add_node(node_id, n["ip"], n["port"], n["token"], n["alias"])
        self.statusBar().showMessage(f"已导入 {len(nodes)} 台节点", 3000)

    def _on_export(self) -> None:
        """导出当前节点列表为 .pcm 配置（§23.4）。"""
        from PyQt5.QtWidgets import QFileDialog
        from common.connect_code import export_config
        nodes = [self.cfg["nodes"][i] for i in range(len(self.cfg.get("nodes", [])))]
        path, _ = QFileDialog.getSaveFileName(
            self, "导出节点配置", "pcmonitor_nodes.pcm", "监控配置 (*.pcm)")
        if not path:
            return
        ok = export_config(nodes, path)
        self.statusBar().showMessage(
            "导出成功" if ok else "导出失败", 3000)

    def _on_discovery_add(self, ip, port, token, alias) -> None:
        node_id = make_host_id(ip, port)
        client_config.upsert_node(self.cfg, node_id, ip, port, token, alias)
        self._add_node(node_id, ip, port, token, alias)

    def _on_context_action(self, action: str, node_id: str) -> None:
        if node_id == LOCAL_NODE_ID:
            return
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
        client_config.upsert_node(self.cfg, conn.node_id, conn.ip, conn.port,
                                  conn.token, alias)
        widget = self.node_manager.get_widget(node_id)
        if widget:
            widget.alias_label.setText(alias)

    # ---------- 信号槽 ----------

    def _on_local_data(self, frame: dict, node_id: str) -> None:
        """本机数据 → 本机仪表盘（不经网络）。"""
        self.local_panel.update_all(frame)

    def _on_data(self, frame: dict, node_id: str) -> None:
        """
        远程节点数据：仅更新节点管理器摘要（状态/RTT/评分），不渲染详情。
        评分由本端本地测量注入（§20.5）。
        """
        self._inject_net_quality(frame, node_id)
        summary = self.local_panel.get_summary(frame)
        widget = self.node_manager.get_widget(node_id)
        if widget:
            widget.update_summary(summary)

    def _inject_net_quality(self, frame: dict, node_id: str) -> None:
        """将本端测量的 RTT/丢包/评分注入帧的 net_quality（§20.5）。"""
        nq = frame.get("net_quality", {})
        if not isinstance(nq, dict):
            nq = {}
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
        frame["net_quality"] = nq

    def _on_status(self, status: str, node_id: str) -> None:
        self.statuses[node_id] = status
        widget = self.node_manager.get_widget(node_id)
        if widget:
            widget.update_status(status)
        self._refresh_top()
        self.statusBar().showMessage(f"{self.nodes[node_id].alias}: {status}", 3000)

    def _on_rtt(self, rtt_ms: float, node_id: str) -> None:
        self.rtts[node_id] = rtt_ms
        widget = self.node_manager.get_widget(node_id)
        if widget:
            widget.update_rtt(rtt_ms)

    def _on_loss(self, loss: float, node_id: str) -> None:
        self.losses[node_id] = loss

    def _refresh_top(self) -> None:
        # 已接入远程节点数（不含本机）
        remote = sum(1 for nid in self.nodes if nid != LOCAL_NODE_ID)
        self.top_label.setText(f"已接入远程节点: {remote}")

    # ---------- 窗口事件 ----------

    def closeEvent(self, event) -> None:
        """关闭确认：确定退出副机端监控？取消则不退出。"""
        reply = QMessageBox.question(
            self, "确认", "确定退出副机端监控？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for conn in self.nodes.values():
                conn.stop()
            if self.local_pack:
                self.local_pack.stop()
            self.listener.stop()
            self.mdns.stop()
            self._save_geometry()
            event.accept()
        else:
            event.ignore()
