# -*- coding: utf-8 -*-
"""EmptyState —— 空状态组件（v5.2 Phase 4-2）。"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.metrics import ThemeMetrics as TM


class EmptyState(QWidget):
    """空状态提示：图标 + 文字 + 可选操作按钮。"""

    def __init__(self, title="暂无数据", subtitle="", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self._title = QLabel(title)
        self._title.setAlignment(Qt.AlignCenter)
        self._title.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: {TM.FONT_SIZE_XL}px; font-weight: bold; background: transparent;")
        layout.addWidget(self._title)

        if subtitle:
            self._sub = QLabel(subtitle)
            self._sub.setAlignment(Qt.AlignCenter)
            self._sub.setStyleSheet(
                f"color: {TC.TEXT_MUTED}; font-size: {TM.FONT_SIZE_MD}px; background: transparent;")
            layout.addWidget(self._sub)

    def set_text(self, title, subtitle=""):
        self._title.setText(title)
        if hasattr(self, '_sub'):
            self._sub.setText(subtitle)
