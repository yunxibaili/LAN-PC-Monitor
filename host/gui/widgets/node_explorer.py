# -*- coding: utf-8 -*-
"""
NodeExplorer —— 节点探索面板（v5.2 Phase 4-3）。

左侧节点列表：搜索 + 过滤 + NodeCard 列表。
纯 UI 组件，不访问 Store。
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QVBoxLayout, QWidget,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S


class NodeListItem(QFrame):
    """节点列表项。"""
    clicked = pyqtSignal(str)

    def __init__(self, node_id, alias, parent=None):
        super().__init__(parent)
        self.node_id = node_id
        self.setFixedHeight(48)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            NodeListItem {{
                background: transparent;
                border-radius: 8px;
            }}
            NodeListItem:hover {{
                background: {TC.BG_HOVER};
            }}
            NodeListItem[active="true"] {{
                background: {TC.BG_CARD};
                border: 1px solid {TC.ACCENT_PRIMARY};
                border-radius: 8px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        self._dot = QLabel("●")
        self._dot.setFixedWidth(12)
        self._dot.setStyleSheet(f"color: {TC.TEXT_DISABLED}; font-size: 10px; background: transparent;")
        layout.addWidget(self._dot)

        info = QVBoxLayout()
        info.setSpacing(0)
        self._name_lbl = QLabel(alias)
        self._name_lbl.setStyleSheet(f"color: {TC.TEXT_PRIMARY}; font-size: 13px; font-weight: 600; background: transparent;")
        info.addWidget(self._name_lbl)
        self._ip_lbl = QLabel("")
        self._ip_lbl.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: 11px; background: transparent;")
        info.addWidget(self._ip_lbl)
        layout.addLayout(info, 1)

        self._score_lbl = QLabel("")
        self._score_lbl.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; background: transparent;")
        layout.addWidget(self._score_lbl)

    def set_info(self, ip="", score="", status="connecting"):
        self._ip_lbl.setText(ip)
        self._score_lbl.setText(score)
        sc = TC.status_color(status)
        self._dot.setStyleSheet(f"color: {sc}; font-size: 10px; background: transparent;")

    def mousePressEvent(self, event):
        self.clicked.emit(self.node_id)
        super().mousePressEvent(event)


class NodeExplorer(QFrame):
    """节点探索面板。"""
    node_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            NodeExplorer {{
                background-color: {TC.BG_SURFACE};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(S.SM, S.SM, S.SM, S.SM)
        layout.setSpacing(S.SM)

        # 搜索框
        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索节点...")
        self._search.setFixedHeight(36)
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: {TC.BG_INPUT};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 8px;
                padding: 0 12px;
                color: {TC.TEXT_PRIMARY};
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {TC.ACCENT_PRIMARY}; }}
        """)
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # 节点标题
        title_row = QHBoxLayout()
        title_row.setContentsMargins(4, 0, 4, 0)
        self._title_lbl = QLabel("所有节点 (0)")
        self._title_lbl.setStyleSheet(f"color: {TC.TEXT_DISABLED}; font-size: 10px; font-weight: 600; background: transparent;")
        title_row.addWidget(self._title_lbl)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        # 节点列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background: transparent; border: none;")
        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(2)
        self._list_layout.addStretch(1)
        scroll.setWidget(self._list_container)
        layout.addWidget(scroll, 1)

    def add_node(self, node_id, alias, ip=""):
        if node_id in self._items:
            return
        item = NodeListItem(node_id, alias)
        item.set_info(ip=ip)
        item.clicked.connect(self.node_selected.emit)
        self._list_layout.insertWidget(self._list_layout.count() - 1, item)
        self._items[node_id] = item
        self._update_title()

    def remove_node(self, node_id):
        item = self._items.pop(node_id, None)
        if item:
            self._list_layout.removeWidget(item)
            item.deleteLater()
        self._update_title()

    def update_node_status(self, node_id, status, score=""):
        item = self._items.get(node_id)
        if item:
            item.set_info(score=score, status=status)

    def _update_title(self):
        self._title_lbl.setText(f"所有节点 ({len(self._items)})")

    def _on_search(self, text):
        text = text.lower()
        for nid, item in self._items.items():
            name_match = text in (item._name_lbl.text() or "").lower()
            ip_match = text in (item._ip_lbl.text() or "").lower()
            item.setVisible(name_match or ip_match or not text)
