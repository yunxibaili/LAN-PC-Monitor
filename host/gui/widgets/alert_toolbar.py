# -*- coding: utf-8 -*-
"""
AlertToolbar —— 告警过滤工具栏（v5.2 Phase 4-5）。

包含：搜索框 + 严重度过滤 + 节点过滤 + 清除按钮。
纯 UI 组件，通过信号通知过滤变化。
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.theme.spacing import ThemeSpacing as S


class AlertToolbar(QFrame):
    """告警过滤工具栏。"""

    filter_changed = pyqtSignal()  # 过滤条件变化
    clear_clicked = pyqtSignal()   # 清除全部

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setStyleSheet(f"""
            AlertToolbar {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(S.MD, S.XS, S.MD, S.XS)
        layout.setSpacing(S.SM)

        # 搜索框
        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索告警...")
        self._search.setFixedHeight(32)
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: {TC.BG_INPUT};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 8px;
                padding: 0 12px;
                color: {TC.TEXT_PRIMARY};
                font-size: TT.BODY['size']px;
            }}
            QLineEdit:focus {{ border-color: {TC.ACCENT_PRIMARY}; }}
        """)
        self._search.textChanged.connect(self._on_filter_changed)
        layout.addWidget(self._search, 1)

        # 严重度过滤
        self._level_combo = QComboBox()
        self._level_combo.setFixedHeight(32)
        self._level_combo.setMinimumWidth(100)
        self._level_combo.addItems(["全部", "Critical", "Warning"])
        self._level_combo.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self._level_combo)

        # 节点过滤
        self._node_combo = QComboBox()
        self._node_combo.setFixedHeight(32)
        self._node_combo.setMinimumWidth(120)
        self._node_combo.addItem("所有节点")
        self._node_combo.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self._node_combo)

        # 清除按钮
        self._clear_btn = QPushButton("清除全部")
        self._clear_btn.setFixedHeight(32)
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TC.TEXT_SECONDARY};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 8px;
                padding: 0 12px;
                font-size: TT.BODY_SMALL['size']px;
            }}
            QPushButton:hover {{
                background: {TC.STATUS_ERROR};
                color: {TC.TEXT_ON_COLOR};
                border-color: {TC.STATUS_ERROR};
            }}
        """)
        self._clear_btn.clicked.connect(self.clear_clicked.emit)
        layout.addWidget(self._clear_btn)

    def _on_filter_changed(self):
        self.filter_changed.emit()

    # ---------- 公开接口 ----------

    def get_level_filter(self):
        """返回过滤等级：None=全部, "red"=Critical, "warn"=Warning。"""
        idx = self._level_combo.currentIndex()
        return [None, "red", "warn"][idx]

    def get_node_filter(self):
        """返回过滤节点：None=全部, node_id=指定节点。"""
        return self._node_combo.currentData()

    def get_search_text(self):
        return self._search.text().strip()

    def update_node_list(self, nodes):
        """更新节点下拉框。nodes: [(node_id, alias), ...]"""
        self._node_combo.clear()
        self._node_combo.addItem("所有节点")
        for node_id, alias in nodes:
            self._node_combo.addItem(alias or node_id, node_id)
