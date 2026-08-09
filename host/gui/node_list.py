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

from common import theme
from common.i18n import tr

log = logging.getLogger("host.gui.node_list")

# 本机节点 ID
LOCAL_NODE_ID = "localhost"


class NodeListItemWidget(QWidget):
    """单个列表项的 widget：别名/IP/状态/RTT/评分。"""

    def __init__(self, alias: str, ip: str, is_local: bool = False):
        super().__init__()
        self.alias = alias
        self.ip = ip
        self.is_local = is_local

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 4, 8, 4)

        left = QVBoxLayout()
        self.alias_label = QLabel(alias)
        self.alias_label.setStyleSheet(
            f"font-weight: bold; font-size: 13px; color: {theme.COLOR_TEXT};")
        self.sub_label = QLabel(f"{ip}  ● {tr('node.connecting')}")
        self.sub_label.setStyleSheet(
            f"font-size: 11px; color: {theme.COLOR_NA};")
        left.addWidget(self.alias_label)
        left.addWidget(self.sub_label)
        root.addLayout(left, 1)

        right = QVBoxLayout()
        self.rtt_label = QLabel("RTT 0.00ms" if is_local else "RTT --")
        self.rtt_label.setStyleSheet(
            f"font-size: 11px; color: {theme.COLOR_NORMAL if is_local else theme.COLOR_NA};")
        self.score_label = QLabel("--" if not is_local else "")
        self.score_label.setStyleSheet(
            f"font-size: 11px; color: {theme.COLOR_NA};")
        right.addWidget(self.rtt_label, 0, Qt.AlignRight)
        right.addWidget(self.score_label, 0, Qt.AlignRight)
        root.addLayout(right, 0)

    def update_status(self, status_text: str) -> None:
        """更新状态行与状态点颜色（status_text 为内部状态码）。"""
        if self.is_local:
            self.sub_label.setText(f"{self.ip}  ● {tr('node.online')}")
            return
        color = (theme.COLOR_NORMAL if status_text == "connected"
                 else theme.COLOR_WARN if status_text in ("reconnecting", "timeout")
                 else theme.COLOR_DANGER)
        dot = "●" if status_text == "connected" else "◐"
        # 状态码 → 显示文案
        disp = {"connected": tr("node.online"),
                "reconnecting": tr("node.reconnecting"),
                "timeout": tr("node.reconnecting"),
                "offline": tr("node.offline"),
                "auth_failed": tr("node.auth_failed")}.get(status_text, status_text)
        self.sub_label.setText(
            f"{self.ip}  <span style='color:{color};'>{dot}</span> {disp}")

    def update_rtt(self, rtt_ms: float) -> None:
        """更新 RTT 小标签（本机节点固定 0.00ms）。"""
        if self.is_local:
            return
        color = theme.rtt_color(rtt_ms)
        self.rtt_label.setText(f"RTT {rtt_ms:.2f}ms")
        self.rtt_label.setStyleSheet(f"font-size: 11px; color: {color};")

    def update_summary(self, summary: dict) -> None:
        """更新评分摘要。"""
        if self.is_local:
            return
        score = summary.get("score", "N/A")
        grade = summary.get("grade", "")
        color = theme.score_color(score)
        text = f"{score}" if grade in ("", "N/A") else f"{score} {grade}"
        self.score_label.setText(text)
        self.score_label.setStyleSheet(f"font-size: 11px; color: {color};")


class NodeListWidget(QListWidget):
    """节点列表控件。"""

    # 右键菜单信号：action(str, node_id) — "remove"/"edit_alias"/"reconnect"
    context_action = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._item_nodes = {}   # node_id → QListWidgetItem

    def add_node(self, node_id: str, alias: str, ip: str,
                 is_local: bool = False) -> QListWidgetItem:
        """添加一个节点列表项。"""
        item = QListWidgetItem()
        widget = NodeListItemWidget(alias, ip, is_local)
        item.setData(Qt.UserRole, node_id)
        item.setSizeHint(widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, widget)
        self._item_nodes[node_id] = item
        return item

    def remove_node(self, node_id: str) -> None:
        """移除一个节点列表项。"""
        item = self._item_nodes.pop(node_id, None)
        if item:
            row = self.row(item)
            self.takeItem(row)

    def get_widget(self, node_id: str):
        """按 node_id 取列表项 widget。"""
        item = self._item_nodes.get(node_id)
        if item:
            return self.itemWidget(item)
        return None

    def select_node(self, node_id: str) -> None:
        """选中某节点。"""
        item = self._item_nodes.get(node_id)
        if item:
            self.setCurrentItem(item)

    def _show_context_menu(self, pos) -> None:
        """右键菜单：移除/编辑别名/手动重连（本机节点不可用）。"""
        item = self.itemAt(pos)
        if item is None:
            return
        node_id = item.data(Qt.UserRole)
        menu = QMenu(self)
        act_edit = menu.addAction(tr("dialog.edit_alias"))
        act_reconnect = menu.addAction(tr("dialog.reconnect"))
        if node_id != LOCAL_NODE_ID:
            menu.addSeparator()
            act_remove = menu.addAction(tr("dialog.remove_node"))
        action = menu.exec_(self.mapToGlobal(pos))
        if action is None:
            return
        if action == act_edit:
            self.context_action.emit("edit_alias", node_id)
        elif action == act_reconnect:
            self.context_action.emit("reconnect", node_id)
        elif node_id != LOCAL_NODE_ID and action == act_remove:
            self.context_action.emit("remove", node_id)
