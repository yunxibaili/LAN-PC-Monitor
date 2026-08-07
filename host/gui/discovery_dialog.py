# -*- coding: utf-8 -*-
"""
监控主机自动发现弹窗（见《技术文档.md》§6.5 / §18.9）。

- 显示当前在线节点（来自 UDP 心跳监听器），支持多选批量添加。
- 已添加的节点（IP+端口已在配置）标记"已添加"并禁用勾选。
- 确认添加后：写入 host_config.json 并回调主窗口创建连接。
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QVBoxLayout)

from common.theme import COLOR_NA
from common.utils import make_host_id

log = logging.getLogger("host.gui.discovery_dialog")


class DiscoveryDialog(QDialog):
    """
    自动发现弹窗。

    :param listener:  DiscoveryListener 实例（提供 get_hosts()）
    :param existing:  已添加的 node_id 集合（用于去重）
    :param on_add:    回调 fn(ip, port, token, alias) 添加节点
    """

    def __init__(self, listener, existing: set, on_add=None, parent=None):
        super().__init__(parent)
        self.listener = listener
        self.existing = existing
        self.on_add = on_add
        self.setWindowTitle("自动扫描节点")
        self.resize(480, 420)
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        hint = QLabel("以下为节点端 UDP 心跳检测到的在线节点，可多选批量添加：")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {COLOR_NA};")
        root.addWidget(hint)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        root.addWidget(self.list_widget, 1)

        bottom = QHBoxLayout()
        refresh_btn = QDialogButtonBox(QDialogButtonBox.Refresh)
        refresh_btn.button(QDialogButtonBox.Refresh).clicked.connect(self._refresh)
        bottom.addWidget(refresh_btn, 0, Qt.AlignLeft)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        bottom.addWidget(buttons, 0, Qt.AlignRight)
        root.addLayout(bottom)

    def _refresh(self) -> None:
        """刷新在线节点列表。"""
        self.list_widget.clear()
        hosts = self.listener.get_hosts()
        if not hosts:
            self.list_widget.addItem("（未发现节点，请确认节点端已启动并放行 UDP 12346）")
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
                item.setText(f"{text}  [已添加]")
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
