# -*- coding: utf-8 -*-
"""
MetricBar —— 指标条组件（v5.2 Phase 4-1B Premium Upgrade）。

动态颜色 + 阈值变化 + 圆角 + 数值右对齐。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.metrics import ThemeMetrics as TM


class MetricBar(QWidget):
    """指标条：标签 + 数值 + 进度条。"""

    def __init__(self, name: str = "", unit: str = "%", parent=None):
        super().__init__(parent)
        self._name = name
        self._unit = unit
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 顶部：标签 + 数值
        top = QHBoxLayout()
        self._name_label = QLabel(self._name)
        self._name_label.setStyleSheet(
            f"color: {TC.TEXT_MUTED}; font-size: {TM.FONT_SIZE_SM}px; background: transparent;")
        top.addWidget(self._name_label)
        top.addStretch(1)
        self._value_label = QLabel("—")
        self._value_label.setStyleSheet(
            f"color: {TC.TEXT_PRIMARY}; font-size: {TM.FONT_SIZE_MD}px; font-weight: bold; background: transparent;")
        top.addWidget(self._value_label)
        layout.addLayout(top)

        # 进度条
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setFixedHeight(6)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {TC.BAR_BG};
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                border-radius: 3px;
                background-color: {TC.BAR_SUCCESS};
            }}
        """)
        layout.addWidget(self._bar)

    def set_metric(self, name: str, value: float, unit: str = "%",
                   warn: float = 80, danger: float = 95) -> None:
        self._name = name
        self._unit = unit
        self._name_label.setText(name)

        if unit == "%":
            self._value_label.setText(f"{value:.1f}%")
        elif unit == "MB/s":
            self._value_label.setText(f"{value:.1f} MB/s")
        elif unit == "GB":
            self._value_label.setText(f"{value:.1f} GB")
        else:
            self._value_label.setText(f"{value:.1f}{unit}")

        clamped = max(0, min(100, value))
        self._bar.setValue(int(clamped))

        color = TC.bar_color(value, warn, danger)
        self._value_label.setStyleSheet(
            f"color: {color}; font-size: {TM.FONT_SIZE_MD}px; font-weight: bold; background: transparent;")
        pct = clamped
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {TC.BAR_BG};
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                border-radius: 3px;
                background-color: {color};
            }}
        """)
