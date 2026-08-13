# -*- coding: utf-8 -*-
"""
StatusBadge —— 状态指示徽标（v5.2 Phase 4-1B）。

ONLINE=绿色 / OFFLINE=红色 / WARNING=黄色
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QWidget

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S

_STATUS_CONFIG = {
    "connected":    ("●", TC.STATUS_ONLINE,  "ONLINE"),
    "online":       ("●", TC.STATUS_ONLINE,  "ONLINE"),
    "connecting":   ("◐", TC.STATUS_WARNING, "CONNECTING"),
    "reconnecting": ("◐", TC.STATUS_WARNING, "RECONNECTING"),
    "timeout":      ("◐", TC.STATUS_WARNING, "TIMEOUT"),
    "offline":      ("○", TC.STATUS_OFFLINE, "OFFLINE"),
    "auth_failed":  ("○", TC.STATUS_ERROR,   "AUTH FAILED"),
    "unknown":      ("○", TC.TEXT_DISABLED,  "UNKNOWN"),
}


class StatusBadge(QWidget):
    """状态指示徽标。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(S.XS)

        self._dot = QLabel("○")
        self._dot.setFixedWidth(14)
        self._dot.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._dot)

        self._text = QLabel("UNKNOWN")
        self._text.setStyleSheet(f"font-size: 11px; background: transparent;")
        layout.addWidget(self._text)

        self.set_status("unknown")

    def set_status(self, status):
        icon, color, label = _STATUS_CONFIG.get(status, _STATUS_CONFIG["unknown"])
        self._dot.setText(icon)
        self._dot.setStyleSheet(f"color: {color}; font-size: 12px; background: transparent;")
        self._text.setText(label)
        self._text.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 600; background: transparent;")

    def get_status(self):
        return self._text.text()
