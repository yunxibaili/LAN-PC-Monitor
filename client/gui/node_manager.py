# -*- coding: utf-8 -*-
"""
副机端节点管理器 —— 已接入节点摘要列表（见《技术文档.md》§6.3 / §20.8）。

- 显示已接入的所有节点列表（含本机）。
- 每个节点项：别名（可编辑）、IP、连接状态（● 在线/离线/重连中）、RTT、评分摘要。
- 本机节点自动添加，置顶显示且别名旁加 [本机] 标签，状态始终"在线"，RTT 0.00ms。
- 点击远程节点不展开详情；悬停显示 Tooltip"该节点详情请在主机端查看"。
- 右键菜单：移除节点、编辑别名、手动重连（本机节点不可移除/重连）。
- 复用 host/gui/node_list 的 NodeListWidget。
"""
import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
                             QWidget)

from common import theme
from host.gui.node_list import LOCAL_NODE_ID, NodeListWidget

log = logging.getLogger("client.gui.node_manager")


class NodeManager(QWidget):
    """副机端节点管理器（本机仪表盘右侧的摘要列表）。"""

    # 信号：add_clicked / scan_clicked / add_local_clicked / context_action(action, node_id)
    add_clicked = pyqtSignal()
    scan_clicked = pyqtSignal()
    add_local_clicked = pyqtSignal()
    context_action = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        title = QLabel("节点管理器")
        title.setObjectName("panel_title")
        root.addWidget(title)

        # 操作按钮
        btns = QHBoxLayout()
        btn_add = QPushButton("添加节点")
        btn_add.clicked.connect(self.add_clicked.emit)
        btns.addWidget(btn_add)
        btn_local = QPushButton("添加本机节点")
        btn_local.setToolTip("一键接入本机采集节点（读取 node_config.json 自动填入）")
        btn_local.clicked.connect(self.add_local_clicked.emit)
        btns.addWidget(btn_local)
        btn_scan = QPushButton("扫描")
        btn_scan.clicked.connect(self.scan_clicked.emit)
        btns.addWidget(btn_scan)
        btns.addStretch(1)
        root.addLayout(btns)

        # 删除按钮：选中远程节点后可显式删除（替代仅右键菜单）
        del_row = QHBoxLayout()
        self.btn_delete = QPushButton("删除选中节点")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        del_row.addWidget(self.btn_delete)
        del_row.addStretch(1)
        root.addLayout(del_row)

        # 节点列表（复用主机端 NodeListWidget）
        self.node_list = NodeListWidget()
        self.node_list.currentItemChanged.connect(self._on_selection_changed)
        self.node_list.context_action.connect(self.context_action.emit)
        root.addWidget(self.node_list, 1)

    def _on_selection_changed(self, current, _previous) -> None:
        """选中项变化：远程节点可删除，本机节点/无选中禁用。"""
        if current is None:
            self.btn_delete.setEnabled(False)
            return
        node_id = current.data(Qt.UserRole)
        self.btn_delete.setEnabled(node_id != LOCAL_NODE_ID)

    def _on_delete_clicked(self) -> None:
        """删除按钮 → 发 context_action('remove', node_id)。"""
        item = self.node_list.currentItem()
        if item is None:
            return
        node_id = item.data(Qt.UserRole)
        if node_id == LOCAL_NODE_ID:
            return  # 本机节点不可删
        self.context_action.emit("remove", node_id)

    # ---------- 转发方法 ----------

    def add_node(self, node_id: str, alias: str, ip: str,
                 is_local: bool = False):
        """添加节点列表项；本机节点别名加 [本机] 标签。"""
        display_alias = f"{alias} [本机]" if is_local else alias
        return self.node_list.add_node(node_id, display_alias, ip, is_local)

    def remove_node(self, node_id: str):
        self.node_list.remove_node(node_id)

    def get_widget(self, node_id: str):
        return self.node_list.get_widget(node_id)

    def select_node(self, node_id: str):
        self.node_list.select_node(node_id)

    def set_tooltip(self, node_id: str) -> None:
        """远程节点悬停提示：详情请在主机端查看（§6.1）。"""
        item = self.node_list._item_nodes.get(node_id)
        if item is not None:
            item.setToolTip("该节点详情请在主机端查看")
