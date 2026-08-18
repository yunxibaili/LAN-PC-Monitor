# -*- coding: utf-8 -*-
"""
监控主机自动发现弹窗（见《README.md》§6.5 / §18.9）。

- 显示当前在线节点（来自 UDP 心跳监听器），支持多选批量添加。
- 已添加的节点（IP+端口已在配置）标记"已添加"并禁用勾选。
- P1-3: Agent 不再广播明文 token，需用户输入 token 确认后才能连接。
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem,
                             QPushButton, QVBoxLayout)

from common.i18n import tr
from common.utils import make_host_id
from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT

log = logging.getLogger("host.gui.discovery_dialog")


class DiscoveryDialog(QDialog):
    """
    自动发现弹窗。

    :param listener:  DiscoveryListener 实例（提供 get_hosts()）
    :param existing:  已添加的 node_id 集合（用于去重）
    :param on_add:    回调 fn(ip, port, token, alias) 添加节点
    """

    def __init__(self, listener, existing: set, on_add=None, on_add_local=None,
                 parent=None):
        super().__init__(parent)
        self.listener = listener
        self.existing = existing
        self.on_add = on_add
        self.on_add_local = on_add_local
        from host.gui.theme.components import remove_help_button
        remove_help_button(self)
        self.setWindowTitle(tr("topbar.scan"))
        self.resize(480, 480)
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        hint = QLabel(tr("discovery.hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {TC.TEXT_DISABLED};")
        root.addWidget(hint)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        root.addWidget(self.list_widget, 1)

        # P1-3: Token 输入行（发现的 Agent 需要用户输入 token 才能连接）
        token_row = QHBoxLayout()
        token_lbl = QLabel("Token:")
        token_lbl.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: TT.BODY_SMALL['size']px;")
        self._token_input = QLineEdit()
        self._token_input.setPlaceholderText("输入 Agent token 以连接（首次连接必需）")
        self._token_input.setEchoMode(QLineEdit.Password)
        self._token_input.setStyleSheet(f"""
            QLineEdit {{
                background: {TC.BG_INPUT};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 6px;
                padding: 6px 10px;
                color: {TC.TEXT_PRIMARY};
                font-size: TT.BODY_SMALL['size']px;
            }}
            QLineEdit:focus {{ border-color: {TC.ACCENT_PRIMARY}; }}
        """)
        token_row.addWidget(token_lbl)
        token_row.addWidget(self._token_input, 1)
        root.addLayout(token_row)

        # 便捷入口
        local_row = QHBoxLayout()
        self.btn_local = QPushButton(tr("discovery.add_local"))
        self.btn_local.setToolTip(tr("discovery.add_local_tip"))
        self.btn_local.clicked.connect(self._on_add_local)
        local_row.addWidget(self.btn_local)
        local_row.addStretch(1)
        root.addLayout(local_row)

        bottom = QHBoxLayout()
        refresh_btn = QPushButton(tr("discovery.refresh"))
        refresh_btn.clicked.connect(self._refresh)
        bottom.addWidget(refresh_btn, 0, Qt.AlignLeft)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        bottom.addWidget(buttons, 0, Qt.AlignRight)
        root.addLayout(bottom)

    def _on_add_local(self) -> None:
        if self.on_add_local:
            self.on_add_local()
            self.accept()

    def _refresh(self) -> None:
        self.list_widget.clear()
        if hasattr(self.listener, "get_hosts"):
            hosts = self.listener.get_hosts()
        else:
            hosts = self.listener or {}
        if not hosts:
            self.list_widget.addItem(tr("discovery.empty"))
            return
        for ip, info in sorted(hosts.items()):
            hostname = info.get("hostname", ip)
            port = info.get("tcp_port", 12345)
            token = info.get("token", "")
            alias = hostname if hostname != ip else f"{ip}:{port}"
            node_id = make_host_id(ip, port)

            text = f"{alias}  ({ip}:{port})"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, {
                "ip": ip, "port": port, "token": token, "alias": alias,
                "node_id": node_id,
            })
            if node_id in self.existing:
                item.setText(tr("discovery.added_tag", text))
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.list_widget.addItem(item)

    def _on_accept(self) -> None:
        token = self._token_input.text().strip()
        if not token:
            token = ""  # 允许空 token（本地节点不需要）
        added = 0
        for item in self.list_widget.selectedItems():
            info = item.data(Qt.UserRole)
            if not info:
                continue
            if info["node_id"] in self.existing:
                continue
            if self.on_add:
                self.on_add(info["ip"], info["port"], token,
                            info["alias"])
                added += 1
        if added:
            log.info("发现弹窗添加 %d 个节点", added)
        self.accept()
