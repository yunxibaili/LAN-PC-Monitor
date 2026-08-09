# -*- coding: utf-8 -*-
"""
副机端节点管理器 —— 已接入节点摘要列表（见《README.md》§6.3 / §20.8）。

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
from common.i18n import tr
from host.gui.node_list import LOCAL_NODE_ID, NodeListWidget

log = logging.getLogger("client.gui.node_manager")


class NodeManager(QWidget):
    """副机端节点管理器（本机仪表盘右侧的摘要列表）。"""

    # 信号：add_clicked / scan_clicked / add_local_clicked / context_action(action, node_id)
    add_clicked = pyqtSignal()
    scan_clicked = pyqtSignal()
    add_local_clicked = pyqtSignal()
    connect_code_clicked = pyqtSignal()
    clipboard_clicked = pyqtSignal()
    import_clicked = pyqtSignal()
    export_clicked = pyqtSignal()
    context_action = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        title = QLabel(tr("node_mgr.title"))
        title.setObjectName("panel_title")
        root.addWidget(title)

        # 操作按钮
        btns = QHBoxLayout()
        btn_add = QPushButton(tr("topbar.add_node"))
        btn_add.clicked.connect(self.add_clicked.emit)
        btns.addWidget(btn_add)
        btn_local = QPushButton(tr("node_mgr.add_local"))
        btn_local.setToolTip(tr("node_mgr.add_local_tip"))
        btn_local.clicked.connect(self.add_local_clicked.emit)
        btns.addWidget(btn_local)
        btn_scan = QPushButton(tr("topbar.scan"))
        btn_scan.clicked.connect(self.scan_clicked.emit)
        btns.addWidget(btn_scan)
        btns.addStretch(1)
        root.addLayout(btns)

        # 便捷连接入口（§2.5）：连接码 / 剪贴板 / 导入 / 导出
        quick = QHBoxLayout()
        btn_code = QPushButton(tr("topbar.connect_code"))
        btn_code.setToolTip(tr("node_mgr.tip_conn_code"))
        btn_code.clicked.connect(self.connect_code_clicked.emit)
        quick.addWidget(btn_code)
        btn_clip = QPushButton(tr("topbar.clipboard"))
        btn_clip.setToolTip(tr("node_mgr.tip_clipboard"))
        btn_clip.clicked.connect(self.clipboard_clicked.emit)
        quick.addWidget(btn_clip)
        btn_imp = QPushButton(tr("topbar.import"))
        btn_imp.setToolTip(tr("node_mgr.tip_import"))
        btn_imp.clicked.connect(self.import_clicked.emit)
        quick.addWidget(btn_imp)
        btn_exp = QPushButton(tr("topbar.export"))
        btn_exp.setToolTip(tr("node_mgr.tip_export"))
        btn_exp.clicked.connect(self.export_clicked.emit)
        quick.addWidget(btn_exp)
        quick.addStretch(1)
        root.addLayout(quick)

        # 节点列表（复用主机端 NodeListWidget）；删除仅通过右键菜单（§6.3）
        self.node_list = NodeListWidget()
        self.node_list.context_action.connect(self.context_action.emit)
        root.addWidget(self.node_list, 1)

    # ---------- 转发方法 ----------

    def add_node(self, node_id: str, alias: str, ip: str,
                 is_local: bool = False):
        """添加节点列表项；本机节点别名加 [本机] 标签。"""
        display_alias = tr("node_mgr.local_tag", alias) if is_local else alias
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
            item.setToolTip(tr("node.detail_in_host"))
