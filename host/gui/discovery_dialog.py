# -*- coding: utf-8 -*-
"""
监控主机自动发现弹窗（见《README.md》§6.5 / §18.9）。

- 显示当前在线节点（来自 UDP 心跳监听器），支持多选批量添加。
- 已添加的节点（IP+端口已在配置）标记"已添加"并禁用勾选。
- 确认添加后：写入 host_config.json 并回调主窗口创建连接。
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QPushButton,
                             QVBoxLayout)

from common.i18n import tr
from common.utils import make_host_id
from host.gui.theme.colors import ThemeColors as TC

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
        remove_help_button(self)   # 移除 Windows 标题栏问号按钮，防闪退
        self.setWindowTitle(tr("topbar.scan"))
        self.resize(480, 420)
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

        # 便捷入口：一键添加本机节点
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
        """一键添加本机节点（复用回调）。"""
        if self.on_add_local:
            self.on_add_local()
            self.accept()

    def _refresh(self) -> None:
        """刷新在线节点列表。"""
        self.list_widget.clear()
        # 兼容：listener 可以是对象（有 get_hosts()）或直接传 dict（合并后的节点）
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
        """确认添加选中的节点。"""
        added = 0
        for item in self.list_widget.selectedItems():
            info = item.data(Qt.UserRole)
            if not info:
                continue
            if info["node_id"] in self.existing:
                continue
            if self.on_add:
                self.on_add(info["ip"], info["port"], info["token"],
                            info["alias"])
            self.existing.add(info["node_id"])
            added += 1
        if added:
            log.info("自动发现添加 %d 台节点", added)
        self.accept()
