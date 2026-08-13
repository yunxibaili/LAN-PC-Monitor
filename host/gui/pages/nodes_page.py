# -*- coding: utf-8 -*-
"""
NodesPage —— 节点管理页（v5.2 Phase 4-3 Redesign）。

左侧 NodeExplorer + 右侧 DetailDashboard。
NodeDetailViewModel 唯一数据来源。
"""
import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSplitter, QVBoxLayout,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.widgets.node_explorer import NodeExplorer
from host.gui.widgets.detail_dashboard import DetailDashboard
from host.gui.pages.base_page import PageBase

log = logging.getLogger("host.gui.nodes_page")


class NodesPage(PageBase):
    """节点管理页：NodeExplorer + DetailDashboard。"""

    PAGE_ID = "nodes"
    node_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._node_detail_vm = None
        self._current_node = None
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Page Header
        header = QHBoxLayout()
        header.setContentsMargins(S.LG, S.SM, S.LG, S.SM)
        title = QLabel("Nodes")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {TC.TEXT_PRIMARY};")
        header.addWidget(title)
        header.addStretch(1)
        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        header.addWidget(self._status_label)
        root.addLayout(header)

        # Splitter: NodeExplorer + DetailDashboard
        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setStyleSheet(f"QSplitter::handle {{ background: {TC.BORDER_DEFAULT}; width: 1px; }}")

        # Left: NodeExplorer
        self._explorer = NodeExplorer()
        self._explorer.node_selected.connect(self._on_node_selected)
        self._splitter.addWidget(self._explorer)

        # Right: DetailDashboard
        self._dashboard = DetailDashboard()
        self._splitter.addWidget(self._dashboard)

        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)

        root.addWidget(self._splitter, 1)

    # ---------- ViewModel 注入 ----------

    def set_view_model(self, vm):
        self._node_detail_vm = vm

    # ---------- 生命周期 ----------

    def on_show(self):
        super().on_show()
        if self._node_detail_vm:
            self._node_detail_vm.refresh_all()
        self._refresh_detail()

    def on_hide(self):
        super().on_hide()

    # ---------- 节点选择 ----------

    def _on_node_selected(self, node_id):
        self._current_node = node_id
        self._refresh_detail()
        self.node_selected.emit(node_id)

    def _refresh_detail(self):
        if not self._current_node or not self._node_detail_vm:
            self._dashboard.update_data(None)
            return
        data = self._node_detail_vm.get_data(self._current_node)
        if data:
            self._dashboard.update_data(data)
        else:
            self._dashboard.update_data(None)

    # ---------- 外部操作 ----------

    def select_node(self, node_id):
        self._explorer._items.get(node_id)
        self._current_node = node_id
        self._refresh_detail()
        self.node_selected.emit(node_id)

    def get_current_node(self):
        return self._current_node

    def _on_context_action(self, action, node_id):
        log.info("节点操作: %s -> %s", action, node_id)
