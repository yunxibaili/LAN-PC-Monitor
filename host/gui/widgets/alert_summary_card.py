# -*- coding: utf-8 -*-
"""
AlertSummaryCard —— 告警统计卡片（v5.2 Phase 4-5）。

展示单个严重度等级的告警数量。
纯 UI 组件，无业务逻辑。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S


class AlertSummaryCard(QFrame):
    """告警统计卡片：等级 + 数量。"""

    def __init__(self, label: str = "", color: str = TC.TEXT_PRIMARY, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedHeight(80)
        self.setMinimumWidth(120)
        self.setStyleSheet(f"""
            AlertSummaryCard {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(S.LG, S.SM, S.LG, S.SM)
        layout.setSpacing(2)

        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: 11px; font-weight: 600; "
            f"letter-spacing: 0.5px; background: transparent;")
        layout.addWidget(self._lbl)

        self._val = QLabel("0")
        self._val.setAlignment(Qt.AlignCenter)
        self._val.setStyleSheet(
            f"color: {color}; font-size: 24px; font-weight: bold; background: transparent;")
        layout.addWidget(self._val)

    def set_value(self, value: int) -> None:
        self._val.setText(str(value))
