# -*- coding: utf-8 -*-
"""
Agent 本机仪表盘主窗口（见《README.md》§5.4 方案 A）。

布局：
    ┌──────────────────────────────────────────────┐
    │ 本机仪表盘（副机端 Agent）                     │
    │ 主机名 | IP | uptime | [本机模式]             │
    ├──────────────────────────────────────────────┤
    │ 连接信息区：IP / 端口 / Token / 连接串 (复制)  │
    ├──────────────────────────────────────────────┤
    │ DetailPanel 分区：CPU/内存/GPU/磁盘/网络/     │
    │ 网络质量/帧率/进程（阈值变色）                 │
    ├──────────────────────────────────────────────┤
    │ 底部：服务状态（HTTP/WS 端口、订阅者数）       │
    └──────────────────────────────────────────────┘

- 本机数据经 LocalCollectorPack 直供（不经网络），与推送数据同构。
- 后台 Agent 服务（WS/REST）在同一进程内运行（--gui 模式）。
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                             QPushButton, QVBoxLayout, QWidget)

from common.gui.theme.colors import ThemeColors as TC
from common.gui.theme.components import remove_help_button
from common.gui.detail_panel import DetailPanel
from common.i18n import tr
from common.utils import get_lan_ip
from agent.local_node import LocalCollectorPack

log = logging.getLogger("agent.gui.main_window")


class AgentDashboardWindow(QMainWindow):
    """副机端 Agent 本机仪表盘主窗口。"""

    def __init__(self, cfg: dict, service_info_getter=None,
                 on_close=None):
        """
        :param cfg:                agent_config.json 配置
        :param service_info_getter: 可选，返回后台服务状态 dict 的回调
                                  （如 {"subscribers": N}），供底部状态显示
        :param on_close:            可选，窗口关闭时调用（如停服务）
        """
        super().__init__()
        self.cfg = cfg
        self._service_info_getter = service_info_getter
        self._on_close = on_close
        self.local_pack = None

        self._restore_geometry()
        self._build_ui()
        self._init_local_node()

    # ---------- 几何 ----------

    def _restore_geometry(self) -> None:
        g = self.cfg.get("window_geometry", {})
        self.setGeometry(g.get("x", 120), g.get("y", 120),
                         g.get("w", 1100), g.get("h", 800))

    def _save_geometry(self) -> None:
        geo = self.geometry()
        self.cfg["window_geometry"] = {
            "x": geo.x(), "y": geo.y(), "w": geo.width(), "h": geo.height(),
        }
        try:
            from agent import config as agent_config
            agent_config.save_config(self.cfg)
        except Exception:
            pass

    # ---------- UI ----------

    def _build_ui(self) -> None:
        self.setWindowTitle(tr("app.title.agent"))
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # 顶部标题行（标题 + 设置齿轮）
        header_row = QHBoxLayout()
        self.header_label = QLabel()
        self.header_label.setObjectName("panel_title")
        header_row.addWidget(self.header_label)
        header_row.addStretch(1)
        btn_settings = QPushButton("⚙")
        btn_settings.setToolTip(tr("settings.title"))
        btn_settings.setFixedWidth(36)
        btn_settings.clicked.connect(self._open_settings)
        header_row.addWidget(btn_settings)
        root.addLayout(header_row)

        # 连接信息区（IP/端口/Token/连接串）
        root.addWidget(self._build_conninfo())

        # 详情面板（分区渲染）
        self.detail_panel = DetailPanel()
        root.addWidget(self.detail_panel, 1)

        # 底部服务状态
        self.status_label = QLabel()
        self.status_label.setStyleSheet(f"color: {TC.TEXT_DISABLED};")
        root.addWidget(self.status_label)

        self.setCentralWidget(central)
        self._update_header()

    def _open_settings(self) -> None:
        """打开设置中心（齿轮按钮入口）。"""
        from common.settings_dialog import SettingsDialog
        dialog = SettingsDialog(parent=self)
        remove_help_button(dialog)
        dialog.exec_()

    def _build_conninfo(self) -> QWidget:
        """连接信息区：IP/端口/Token/连接串 + 复制按钮（§5.4）。"""
        box = QWidget()
        lay = QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)

        ip = get_lan_ip(self.cfg.get("preferred_iface", ""))
        port = self.cfg.get("http_port", 12345)
        token = self.cfg.get("token", "")
        connect_uri = f"pcmonitor://{ip}:{port}?token={token}"

        def _mk(name, text):
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(2)
            lbl = QLabel(name)
            lbl.setStyleSheet(f"color: {TC.TEXT_DISABLED};")
            edit = QLineEdit(text)
            edit.setReadOnly(True)
            edit.setMaximumWidth(240)
            h.addWidget(lbl)
            h.addWidget(edit)
            return w

        lay.addWidget(_mk(tr("conninfo.ip"), ip))
        lay.addWidget(_mk(tr("conninfo.port"), str(port)))
        lay.addWidget(_mk(tr("conninfo.token"), token))
        lay.addStretch(1)

        # 复制连接串按钮
        copy_btn = QPushButton(tr("conninfo.copy_uri"))
        copy_btn.clicked.connect(lambda: self._copy(connect_uri))
        lay.addWidget(copy_btn)
        return box

    @staticmethod
    def _copy(text: str) -> None:
        from PyQt5.QtWidgets import QApplication
        try:
            QApplication.clipboard().setText(text)
        except Exception:
            pass

    # ---------- 本机采集 ----------

    def _init_local_node(self) -> None:
        """启动本地采集包，数据直供仪表盘（不经网络）。"""
        self.local_pack = LocalCollectorPack(self.cfg)
        self.local_pack.local_data.connect(self._on_local_data)
        self.local_pack.start()
        log.info("本机仪表盘采集已启动")

    def _on_local_data(self, frame: dict, _node_id: str) -> None:
        """本机数据帧 → 详情面板。"""
        self.detail_panel.update_all(frame)
        self._update_header(frame)
        self._update_status(frame)

    # ---------- 状态显示 ----------

    def _update_header(self, frame: dict | None = None) -> None:
        sys_info = (frame or {}).get("system", {})
        ip = sys_info.get("local_ip") or get_lan_ip(
            self.cfg.get("preferred_iface", ""))
        self.header_label.setText(
            f"{tr('app.title.agent')}  |  {ip}  |  [{tr('node.local_mode')}]")

    def _update_status(self, frame: dict | None = None) -> None:
        """底部服务状态：端口 + 订阅者数。"""
        port = self.cfg.get("http_port", 12345)
        subs = 0
        if self._service_info_getter:
            try:
                info = self._service_info_getter()
                subs = info.get("subscribers", 0)
            except Exception:
                pass
        self.status_label.setText(
            f"HTTP/WS :{port}   |   订阅者 {subs}   |   "
            f"{tr('topbar.ready')}")

    # ---------- 窗口事件 ----------

    def closeEvent(self, event) -> None:
        """关闭：停本机采集 + 触发 on_close（停后台服务）。"""
        if self.local_pack:
            self.local_pack.stop()
        if self._on_close:
            try:
                self._on_close()
            except Exception:
                pass
        self._save_geometry()
        event.accept()
