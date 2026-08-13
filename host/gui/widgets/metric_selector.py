# -*- coding: utf-8 -*-
"""
MetricSelector —— 指标选择器（v5.2 Phase 4-4）。

水平 Tab 栏：CPU / GPU / RAM / Network / FPS。
纯 UI 组件，通过 signal 通知选择变化。
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S


class MetricTab(QPushButton):
    """单个指标 Tab。"""

    def __init__(self, key, label, icon="", parent=None):
        super().__init__(label, parent)
        self.metric_key = key
        self.setCheckable(True)
        self.setFixedHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style(False)

    def _update_style(self, checked):
        if checked:
            self.setStyleSheet(f"""
                MetricTab {{
                    background: {TC.ACCENT_PRIMARY};
                    color: {TC.TEXT_ON_COLOR};
                    border: none;
                    border-radius: 8px;
                    padding: 0 16px;
                    font-size: 12px;
                    font-weight: 600;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                MetricTab {{
                    background: transparent;
                    color: {TC.TEXT_SECONDARY};
                    border: 1px solid {TC.BORDER_DEFAULT};
                    border-radius: 8px;
                    padding: 0 16px;
                    font-size: 12px;
                    font-weight: 500;
                }}
                MetricTab:hover {{
                    background: {TC.BG_HOVER};
                    color: {TC.TEXT_PRIMARY};
                    border-color: {TC.BORDER_SUBTLE};
                }}
            """)

    def setChecked(self, checked):
        super().setChecked(checked)
        self._update_style(checked)


class MetricSelector(QFrame):
    """指标选择器：水平 Tab 栏。"""

    metric_changed = pyqtSignal(str)

    # 默认指标定义
    METRICS = [
        ("cpu", "CPU"),
        ("gpu", "GPU"),
        ("ram", "RAM"),
        ("net", "Network"),
        ("fps", "FPS"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tabs = {}
        self._current = "cpu"
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(48)
        self.setStyleSheet(f"""
            MetricSelector {{
                background-color: {TC.BG_SURFACE};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(S.SM, S.XS, S.SM, S.XS)
        layout.setSpacing(S.XS)

        for key, label in self.METRICS:
            tab = MetricTab(key, label)
            tab.clicked.connect(lambda checked, k=key: self._on_tab_clicked(k))
            layout.addWidget(tab)
            self._tabs[key] = tab

        layout.addStretch(1)

        # 默认选中 CPU
        self._tabs["cpu"].setChecked(True)

    def _on_tab_clicked(self, key):
        if key == self._current:
            return
        old = self._tabs.get(self._current)
        if old:
            old.setChecked(False)
        self._current = key
        self._tabs[key].setChecked(True)
        self.metric_changed.emit(key)

    def get_current(self):
        return self._current

    def set_current(self, key):
        if key in self._tabs and key != self._current:
            old = self._tabs.get(self._current)
            if old:
                old.setChecked(False)
            self._current = key
            self._tabs[key].setChecked(True)
