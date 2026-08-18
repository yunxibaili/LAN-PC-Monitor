# -*- coding: utf-8 -*-
"""
ResourceCard —— 资源监控卡（v5.2 Phase 4-3）。

纯 UI 组件：环形进度 + 数值 + 标签。
用于 NodesPage DetailDashboard 中的 CPU/GPU/RAM/Disk 指标。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.theme.spacing import ThemeSpacing as S


def _draw_arc(painter, cx, cy, radius, value, color):
    pen = QPen(QColor(color), 4, Qt.SolidLine, Qt.RoundCap)
    painter.setPen(pen)
    span = int(value / 100 * 360 * 16) if value > 0 else 0
    painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2,
                    90 * 16, -span)
    painter.setPen(QPen(QColor(TC.BAR_BG), 4, Qt.SolidLine, Qt.RoundCap))
    painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2,
                    90 * 16, -360 * 16)


class ResourceCard(QFrame):
    """资源监控卡：环形进度 + 数值。"""

    def __init__(self, title="", unit="%", parent=None):
        super().__init__(parent)
        self._title = title
        self._unit = unit
        self._value = 0.0
        self._sub = ""
        self.setFixedHeight(90)
        self.setStyleSheet(f"""
            ResourceCard {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(S.SM, 8, S.SM, 8)
        layout.setSpacing(2)

        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: TT.CAPTION['size']px; background: transparent;")
        layout.addWidget(self._title_lbl)

        # Ring + value
        ring_row = QHBoxLayout()
        ring_row.setSpacing(S.SM)
        ring_row.setContentsMargins(0, 0, 0, 0)
        self._ring = QWidget()
        self._ring.setFixedSize(52, 52)
        self._ring.paintEvent = self._paint_ring
        ring_row.addWidget(self._ring)
        self._val_lbl = QLabel("—")
        self._val_lbl.setStyleSheet(
            f"color: {TC.TEXT_PRIMARY}; font-size: TT.TITLE_SMALL['size']px; font-weight: bold; background: transparent;")
        ring_row.addWidget(self._val_lbl, 1)
        ring_row.addStretch(1)
        layout.addLayout(ring_row)

        self._sub_lbl = QLabel("")
        self._sub_lbl.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: TT.CAPTION['size']px; background: transparent;")
        layout.addWidget(self._sub_lbl)

    def set_resource(self, value, unit="%", sub=""):
        self._value = value
        self._unit = unit
        self._sub = sub
        self._val_lbl.setText(f"{value:.0f}{unit}")
        color = TC.bar_color(value)
        self._val_lbl.setStyleSheet(
            f"color: {color}; font-size: TT.TITLE_SMALL['size']px; font-weight: bold; background: transparent;")
        self._sub_lbl.setText(sub)
        self._ring.update()

    def _paint_ring(self, event):
        painter = QPainter(self._ring)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self._ring.width(), self._ring.height()
        cx, cy, r = w // 2, h // 2, min(w, h) // 2 - 4
        color = TC.bar_color(self._value)
        _draw_arc(painter, cx, cy, r, self._value, color)
        painter.setPen(QColor(TC.TEXT_PRIMARY))
        painter.setFont(painter.font())
        painter.drawText(0, 0, w, h, Qt.AlignCenter, f"{self._value:.0f}")
