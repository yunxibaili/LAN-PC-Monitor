# -*- coding: utf-8 -*-
"""
StatusPill —— 状态胶囊（v5.5 重设计）。

彩色圆点 + 文字，按状态变色（在线绿/警告橙/危险红/离线灰）。
纯 UI 组件，只 import Theme。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QWidget

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT


class StatusPill(QWidget):
    """状态胶囊：圆点 + 文本。"""

    _TEXT = {"connected": "ONLINE", "online": "ONLINE",
             "connecting": "CONNECTING", "reconnecting": "CONNECTING",
             "timeout": "TIMEOUT", "offline": "OFFLINE",
             "auth_failed": "AUTH FAILED"}

    def __init__(self, status="connecting", parent=None):
        super().__init__(parent)
        self._status = status
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self._dot = QLabel("●")
        self._dot.setStyleSheet("font-size: 9px; background: transparent;")
        layout.addWidget(self._dot)
        self._text = QLabel("")
        self._text.setStyleSheet(
            f"font-size: {TT.CAPTION['size']}px; font-weight: 600;"
            f" background: transparent;")
        layout.addWidget(self._text)
        self.set_status(self._status)

    def set_status(self, status):
        self._status = status
        color = TC.status_color(status)
        text = self._TEXT.get(status, status.upper())
        self._dot.setStyleSheet(
            f"color: {color}; font-size: 9px; background: transparent;")
        self._text.setStyleSheet(
            f"color: {color}; font-size: {TT.CAPTION['size']}px;"
            f" font-weight: 600; background: transparent;")
        self._text.setText(text)
