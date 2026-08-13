# -*- coding: utf-8 -*-
"""
MetricCard —— 指标统计卡（v5.2 Phase 4-1B）。

支持：标题 + 大数字 + 单位 + 趋势箭头 + 状态颜色。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S


class MetricCard(QFrame):
    """指标统计卡。"""

    def __init__(self, title="", value="0", unit="", color=None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self.setStyleSheet(f"""
            MetricCard {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
                padding: {S.SM}px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(S.MD, 8, S.MD, 8)
        layout.setSpacing(2)

        self._title = QLabel(title)
        self._title.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        layout.addWidget(self._title)

        num_row = QHBoxLayout()
        num_row.setSpacing(4)
        self._value = QLabel(value)
        self._value.setStyleSheet(
            f"color: {color or TC.TEXT_PRIMARY}; font-size: 32px; font-weight: bold; background: transparent;")
        num_row.addWidget(self._value)
        self._unit = QLabel(unit)
        self._unit.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        num_row.addWidget(self._unit)
        num_row.addStretch(1)
        layout.addLayout(num_row)

        self._trend = QLabel("")
        self._trend.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: 11px; background: transparent;")
        layout.addWidget(self._trend)

    def set_value(self, value, unit="", color=None, trend=""):
        self._value.setText(str(value))
        self._unit.setText(unit)
        if color:
            self._value.setStyleSheet(
                f"color: {color}; font-size: 32px; font-weight: bold; background: transparent;")
        if trend:
            self._trend.setText(trend)
            trend_color = TC.STATUS_ONLINE if trend.startswith("↑") else TC.STATUS_ERROR if trend.startswith("↓") else TC.TEXT_SECONDARY
            self._trend.setStyleSheet(f"color: {trend_color}; font-size: 11px; background: transparent;")
