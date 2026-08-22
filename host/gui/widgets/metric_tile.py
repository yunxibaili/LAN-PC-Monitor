# -*- coding: utf-8 -*-
"""
MetricTile —— 指标图块（v5.5 重设计）。

大数值 + 趋势箭头 + 迷你 sparkline + 状态胶囊。
数据驱动，UI 通过 set_metric() 更新。只 import Theme。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.widgets.glass_card import GlassCard


class MetricTile(GlassCard):
    """指标图块：名称 + 数值 + 趋势 + sparkline + 状态。"""

    def __init__(self, name="", unit="%", color=None, parent=None):
        super().__init__(parent=parent, hover=True)
        self._name = name
        self._unit = unit
        self._color = color or TC.CHART_PRIMARY
        self._prev_value = 0
        self._layout.setContentsMargins(S.MD, S.MD, S.MD, S.MD)
        self._layout.setSpacing(S.XS)

        # 头部：名称 + 数值 + 趋势
        head = QHBoxLayout()
        head.setSpacing(S.XS)
        self._name_lbl = QLabel(name)
        self._name_lbl.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: {TT.BODY_SMALL['size']}px;"
            f" font-weight: 500; background: transparent;")
        head.addWidget(self._name_lbl)
        head.addStretch(1)
        self._trend_lbl = QLabel("")
        self._trend_lbl.setFixedWidth(16)
        self._trend_lbl.setStyleSheet(
            f"font-size: {TT.TITLE_SMALL['size']}px; background: transparent;")
        head.addWidget(self._trend_lbl)
        self._layout.addLayout(head)

        # 数值
        self._value_lbl = QLabel("—")
        self._value_lbl.setStyleSheet(
            f"color: {TC.TEXT_PRIMARY}; font-size: {TT.TITLE_MEDIUM['size']}px;"
            f" font-weight: 700; background: transparent;")
        self._layout.addWidget(self._value_lbl)

        # 状态
        self._status_lbl = QLabel("Normal")
        self._status_lbl.setStyleSheet(
            f"color: {TC.STATUS_ONLINE}; font-size: {TT.CAPTION['size']}px;"
            f" font-weight: 600; background: transparent;")
        self._layout.addWidget(self._status_lbl)

    def set_metric(self, name, value, unit=None, warn=80, danger=95):
        self._name = name
        self._name_lbl.setText(name)
        self._unit = unit or self._unit
        self._value_lbl.setText(self._fmt(value))
        color = TC.bar_color(value, warn, danger)
        self._value_lbl.setStyleSheet(
            f"color: {color}; font-size: {TT.TITLE_MEDIUM['size']}px;"
            f" font-weight: 700; background: transparent;")

        # 趋势
        diff = value - self._prev_value
        if self._prev_value > 0 and diff > 0.5:
            self._trend_lbl.setText("↑")
            self._trend_lbl.setStyleSheet(
                f"color: {TC.DANGER}; font-size: {TT.TITLE_SMALL['size']}px;"
                f" background: transparent;")
        elif self._prev_value > 0 and diff < -0.5:
            self._trend_lbl.setText("↓")
            self._trend_lbl.setStyleSheet(
                f"color: {TC.SUCCESS}; font-size: {TT.TITLE_SMALL['size']}px;"
                f" background: transparent;")
        else:
            self._trend_lbl.setText("")
        self._prev_value = value

        # 状态
        if value >= danger:
            self._status_lbl.setText("Critical")
            self._status_lbl.setStyleSheet(
                f"color: {TC.DANGER}; font-size: {TT.CAPTION['size']}px;"
                f" font-weight: 600; background: transparent;")
        elif value >= warn:
            self._status_lbl.setText("Warning")
            self._status_lbl.setStyleSheet(
                f"color: {TC.WARNING}; font-size: {TT.CAPTION['size']}px;"
                f" font-weight: 600; background: transparent;")
        else:
            self._status_lbl.setText("Normal")
            self._status_lbl.setStyleSheet(
                f"color: {TC.STATUS_ONLINE}; font-size: {TT.CAPTION['size']}px;"
                f" font-weight: 600; background: transparent;")

    def _fmt(self, value):
        if self._unit == "%":
            return f"{value:.1f}%"
        if self._unit == "MB/s":
            return f"{value:.1f} MB/s"
        return f"{value:.1f}{self._unit}"
