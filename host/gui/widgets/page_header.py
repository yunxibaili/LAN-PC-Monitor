# -*- coding: utf-8 -*-
"""PageHeader —— 页面标题栏（v5.2 Phase 4-2）。"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.metrics import ThemeMetrics as TM


class PageHeader(QWidget):
    """页面标题：标题 + 操作按钮。"""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TM.SPACING_MD)

        self._title = QLabel(title)
        self._title.setStyleSheet(
            f"font-size: {TM.FONT_SIZE_XL}px; font-weight: bold; color: {TC.TEXT_PRIMARY};")
        layout.addWidget(self._title)
        layout.addStretch(1)

        self._buttons = QWidget()
        self._btn_layout = QHBoxLayout(self._buttons)
        self._btn_layout.setContentsMargins(0, 0, 0, 0)
        self._btn_layout.setSpacing(TM.SPACING_SM)
        layout.addWidget(self._buttons)

    def add_button(self, text, callback=None):
        btn = QPushButton(text)
        btn.setFixedHeight(32)
        if callback:
            btn.clicked.connect(callback)
        self._btn_layout.addWidget(btn)
        return btn

    def set_title(self, title):
        self._title.setText(title)
