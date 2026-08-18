# -*- coding: utf-8 -*-
"""
MetricBar —— 指标条组件（v5.4 专业监控面板风格）。

布局：标签 + 数值（右对齐）+ 进度条
进度条：8px 高度，圆角，阈值变色
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT


class MetricBar(QWidget):
    """指标条：标签 + 数值 + 进度条。"""

    def __init__(self, name: str = "", unit: str = "%", parent=None):
        super().__init__(parent)
        self._name = name
        self._unit = unit
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)

        # 顶部：标签 + 数值
        top = QHBoxLayout()
        self._name_label = QLabel(self._name)
        self._name_label.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: {TT.BODY_SMALL['size']}px;"
            f" font-weight: 500; background: transparent;")
        top.addWidget(self._name_label)
        top.addStretch(1)
        self._value_label = QLabel("—")
        self._value_label.setStyleSheet(
            f"color: {TC.TEXT_PRIMARY}; font-size: {TT.TITLE_MEDIUM['size']}px;"
            f" font-weight: 700; background: transparent;")
        top.addWidget(self._value_label)
        layout.addLayout(top)

        # 进度条（8px 高度）
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setFixedHeight(8)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {TC.BAR_BG};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
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
            f"color: {color}; font-size: {TT.TITLE_MEDIUM['size']}px;"
            f" font-weight: 700; background: transparent;")
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {TC.BAR_BG};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background-color: {color};
            }}
        """)
