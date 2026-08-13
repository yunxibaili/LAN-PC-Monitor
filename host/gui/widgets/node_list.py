# -*- coding: utf-8 -*-
"""
监控主机左侧节点列表（见《README.md》§6.4 / §18.1）。

列表项布局：
    ┌─────────────────────────────────────────────────────────┐
    │ 游戏主机                          [RTT 0.45ms] [98 优秀] │
    │ 192.168.1.100  ● 已连接                                  │
    └─────────────────────────────────────────────────────────┘

- 左侧：别名（粗体）+ IP + 状态指示点（● 绿=已连接 / ◐ 橙=重连中 / ○ 红=离线/鉴权失败）
- 右侧：RTT 小标签（阈值变色）+ 评分小标签（阈值变色）
- 本机节点固定置顶，RTT 0.00ms，不可移除/重连
- 右键菜单：移除节点、编辑别名、手动重连（本机节点不可用）
"""
import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QListWidget,
                             QListWidgetItem, QMenu, QVBoxLayout, QWidget)

from host.gui.theme import (
    COLOR_TEXT, COLOR_NA, COLOR_NORMAL, COLOR_WARN, COLOR_DANGER, rtt_color, score_color,
)
from common.constants import LOCAL_NODE_ID
from common.i18n import tr

log = logging.getLogger("host.gui.widgets.node_list")


class NodeListItemWidget(QWidget):
    """单个列表项的 widget：别名/IP/状态/RTT/评分。"""

    def __init__(self, alias: str, ip: str, is_local: bool = False):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        left = QVBoxLayout()
        left.setSpacing(0)
        self._alias = QLabel(alias)
        self._alias.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {COLOR_TEXT};")
        left.addWidget(self._alias)
        self._ip = QLabel(ip)
        self._ip.setStyleSheet(f"font-size: 11px; color: {COLOR_NA};")
        left.addWidget(self._ip)
        layout.addLayout(left, 1)

        right = QVBoxLayout()
        right.setSpacing(0)
        self._status = QLabel("●")
        status_color = COLOR_NORMAL if is_local else COLOR_NA
        self._status.setStyleSheet(f"font-size: 11px; color: {status_color};")
        right.addWidget(self._status)
        self._rtt = QLabel("")
        self._rtt.setStyleSheet(f"font-size: 11px; color: {COLOR_NA};")
        right.addWidget(self._rtt)
        layout.addLayout(right)

        self._score = QLabel("")
        self._score.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLOR_NA};")
        layout.addWidget(self._score)

    def set_status(self, status_text: str):
        color = (COLOR_NORMAL if status_text == "connected"
                 else COLOR_WARN if status_text in ("connecting", "reconnecting")
                 else COLOR_DANGER)
        self._status.setStyleSheet(f"font-size: 11px; color: {color};")

    def set_rtt(self, rtt_ms: float):
        color = rtt_color(rtt_ms)
        self._rtt.setText(f"RTT {rtt_ms:.2f}ms")
        self._rtt.setStyleSheet(f"font-size: 11px; color: {color};")

    def set_score(self, score, grade=""):
        color = score_color(score)
        self._score.setText(f"{score} {grade}")
        self._score.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {color};")


class NodeListWidget(QListWidget):
    """节点列表组件。"""
    node_selected = pyqtSignal(str)
    node_removed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = {}
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemClicked.connect(self._on_click)

    def add_node(self, node_id, alias, ip, is_local=False):
        widget = NodeListItemWidget(alias, ip, is_local)
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        item.setData(Qt.UserRole, node_id)
        self.addItem(item)
        self.setItemWidget(item, widget)
        self._items[node_id] = (item, widget)

    def update_node_status(self, node_id, status):
        if node_id in self._items:
            _, widget = self._items[node_id]
            widget.set_status(status)

    def update_node_rtt(self, node_id, rtt_ms):
        if node_id in self._items:
            _, widget = self._items[node_id]
            widget.set_rtt(rtt_ms)

    def update_node_score(self, node_id, score, grade=""):
        if node_id in self._items:
            _, widget = self._items[node_id]
            widget.set_score(score, grade)

    def remove_node(self, node_id):
        if node_id in self._items:
            item, _ = self._items.pop(node_id)
            self.takeItem(self.row(item))

    def select_node(self, node_id):
        if node_id in self._items:
            item, _ = self._items[node_id]
            self.setCurrentItem(item)

    def _on_click(self, item):
        node_id = item.data(Qt.UserRole)
        if node_id:
            self.node_selected.emit(node_id)

    def _show_context_menu(self, pos):
        item = self.itemAt(pos)
        if not item:
            return
        node_id = item.data(Qt.UserRole)
        if node_id == LOCAL_NODE_ID:
            return

        menu = QMenu(self)
        act_remove = menu.addAction(tr("node.remove"))
        action = menu.exec_(self.mapToGlobal(pos))
        if action == act_remove:
            self.node_removed.emit(node_id)
