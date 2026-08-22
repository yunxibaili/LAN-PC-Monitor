# -*- coding: utf-8 -*-
"""
StatCard —— 统计卡（v5.5 重设计）。

左侧 3px 彩色边 + 标签 + 大数值 + 副文本。
纯 UI 组件，只 import Theme。
"""
from PyQt5.QtWidgets import QVBoxLayout

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.metrics import ThemeMetrics as TM
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.widgets.glass_card import GlassCard


class StatCard(GlassCard):
    """统计卡：彩色左边 + 标签 + 数值 + 副文本。"""

    def __init__(self, label="", value="—", accent=None, sub="", parent=None):
        super().__init__(parent=parent, hover=False)
        self._accent = accent or TC.ACCENT_PRIMARY
        self._size = 30
        self.setMinimumHeight(88)
        self._layout.setContentsMargins(16, 13, 16, 13)
        self._layout.setSpacing(2)

        self._label_lbl = self._label(label)
        self._value_lbl = self._value(str(value))
        self._sub_lbl = self._sub(sub)

        self._layout.addWidget(self._label_lbl)
        self._layout.addWidget(self._value_lbl)
        self._layout.addWidget(self._sub_lbl)
        self._paint_border()
        # 兼容旧接口：_val 同 _value_lbl
        self._val = self._value_lbl

    def _paint_border(self):
        self.setStyleSheet(f"""
            QFrame#glassCard {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-left: 3px solid {self._accent};
                border-radius: {TM.RADIUS_LG}px;
            }}
        """)

    def _label(self, text):
        lbl = self._mk(text)
        lbl.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: {TT.CAPTION['size']}px;"
            f" font-weight: 600; letter-spacing: 0.5px; background: transparent;")
        return lbl

    def _value(self, text):
        lbl = self._mk(text)
        lbl.setStyleSheet(
            f"color: {TC.TEXT_PRIMARY}; font-size: {self._size}px;"
            f" font-weight: 700; background: transparent;")
        return lbl

    def _sub(self, text):
        lbl = self._mk(text)
        lbl.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: {TT.BODY_SMALL['size']}px;"
            f" background: transparent;")
        return lbl

    def _mk(self, text):
        from PyQt5.QtWidgets import QLabel
        lbl = QLabel(text)
        return lbl

    def set_value(self, value, sub=None, color=None):
        self._value_lbl.setText(str(value))
        c = color or TC.TEXT_PRIMARY
        self._value_lbl.setStyleSheet(
            f"color: {c}; font-size: {self._size}px;"
            f" font-weight: 700; background: transparent;")
        if sub is not None:
            self._sub_lbl.setText(sub)
