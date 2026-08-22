# -*- coding: utf-8 -*-
"""
RingGauge —— 环形进度（v5.5 重设计）。

背景环（浅灰）+ 前景环（按阈值变色）+ 中心数值。
用 QPainter 绘制，颜色 token 必须为纯 hex（QColor 可解析）。
纯 UI 组件，只 import Theme。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT


class RingGauge(QWidget):
    """环形进度：value 0-100，按阈值变色。"""

    def __init__(self, label="", value=0.0, unit="%", parent=None):
        super().__init__(parent)
        self._label = label
        self._value = value
        self._unit = unit
        self._warn = 80
        self._danger = 95
        self._setup_ui()

    def _setup_ui(self):
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(72, 72)
        self._value_lbl = QLabel("--", self)
        self._value_lbl.setAlignment(Qt.AlignCenter)
        self._value_lbl.setGeometry(0, 0, 72, 72)
        self._value_lbl.setStyleSheet(
            f"color: {TC.TEXT_PRIMARY}; font-size: {TT.TITLE_SMALL['size']}px;"
            f" font-weight: 700; background: transparent;")
        self.refresh()

    def set_value(self, value, unit=None):
        self._value = value or 0
        if unit is not None:
            self._unit = unit
        self.refresh()

    def refresh(self):
        v = max(0, min(100, self._value))
        self._value_lbl.setText(f"{v:.0f}%")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy, r = w // 2, h // 2, min(w, h) // 2 - 6
        span = int(self._value / 100 * 360 * 16)

        # 背景环
        painter.setPen(QPen(QColor(TC.BAR_BG), 5, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(cx - r, cy - r, r * 2, r * 2, 90 * 16, -360 * 16)

        # 前景环（按阈值变色）
        color = TC.bar_color(self._value, self._warn, self._danger)
        painter.setPen(QPen(QColor(color), 5, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(cx - r, cy - r, r * 2, r * 2, 90 * 16, -span)

        painter.end()
        super().paintEvent(event)
