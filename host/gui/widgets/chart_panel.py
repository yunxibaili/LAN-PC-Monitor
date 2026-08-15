# -*- coding: utf-8 -*-
"""
ChartPanel —— 图表面板（v5.2 Phase 4-4）。

包含：
- ChartWidget（大面积图表）
- MetricSummaryCards（Current / Average / Peak / Status）

纯 UI 组件，不访问 Store。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.widgets.chart_widget import ChartWidget


class SummaryCard(QFrame):
    """汇总卡片：Current / Average / Peak / Status。"""

    def __init__(self, title="", value="—", color=None, size=20, parent=None):
        super().__init__(parent)
        self._title = title
        self._size = size
        self.setFixedHeight(72)
        self.setStyleSheet(f"""
            SummaryCard {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(S.MD, S.SM, S.MD, S.SM)
        layout.setSpacing(2)

        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: 10px; font-weight: 600; "
            f"letter-spacing: 0.5px; background: transparent;")
        layout.addWidget(self._title_lbl)

        self._value_lbl = QLabel(str(value))
        self._value_lbl.setStyleSheet(
            f"color: {color or TC.TEXT_PRIMARY}; font-size: {size}px; font-weight: bold; "
            f"background: transparent;")
        layout.addWidget(self._value_lbl)

        self._sub_lbl = QLabel("")
        self._sub_lbl.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: 11px; background: transparent;")
        layout.addWidget(self._sub_lbl)

    def set_value(self, value, sub="", color=None):
        self._value_lbl.setText(str(value))
        c = color or TC.TEXT_PRIMARY
        self._value_lbl.setStyleSheet(
            f"color: {c}; font-size: {self._size}px; font-weight: bold; background: transparent;")
        self._sub_lbl.setText(sub)


class ChartPanel(QFrame):
    """图表面板：ChartWidget + SummaryCards。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            ChartPanel {{
                background-color: {TC.BG_SURFACE};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(S.SM, S.SM, S.SM, S.SM)
        layout.setSpacing(S.SM)

        # 图表区
        self._chart = ChartWidget(title="CPU", y_range=(0, 100))
        self._chart.setMinimumHeight(280)
        self._chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self._chart, 1)

        # Summary Cards (4 列)
        cards_grid = QGridLayout()
        cards_grid.setSpacing(S.SM)
        self._current_card = SummaryCard("CURRENT")
        self._avg_card = SummaryCard("AVERAGE")
        self._peak_card = SummaryCard("PEAK")
        self._status_card = SummaryCard("STATUS")
        cards_grid.addWidget(self._current_card, 0, 0)
        cards_grid.addWidget(self._avg_card, 0, 1)
        cards_grid.addWidget(self._peak_card, 0, 2)
        cards_grid.addWidget(self._status_card, 0, 3)
        layout.addLayout(cards_grid)

    def get_chart(self):
        return self._chart

    def update_summary(self, current=None, average=None, peak=None,
                       status_text="", status_color=None, unit="%"):
        """更新汇总卡片。"""
        if current is not None:
            self._current_card.set_value(f"{current:.1f}{unit}")
        if average is not None:
            self._avg_card.set_value(f"{average:.1f}{unit}")
        if peak is not None:
            self._peak_card.set_value(f"{peak:.1f}{unit}")
        if status_text:
            self._status_card.set_value(status_text, color=status_color)

    def clear_summary(self):
        self._current_card.set_value("—")
        self._avg_card.set_value("—")
        self._peak_card.set_value("—")
        self._status_card.set_value("—")

    def clear(self):
        self._chart.clear()
        self.clear_summary()
