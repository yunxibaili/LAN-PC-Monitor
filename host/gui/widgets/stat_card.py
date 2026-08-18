# -*- coding: utf-8 -*-
"""
StatCard —— 统计卡片组件（v5.4 Gentelella 风格）。

布局：彩色图标圆 + Label + 大数值 + 副文本
参考：Gentelella stat 组件（icon + content）
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT


class StatCard(QFrame):
    """统计卡片：图标 + 标签 + 数值 + 副文本。"""

    def __init__(self, title="", value="0", icon_color=None, parent=None):
        super().__init__(parent)
        self._icon_color = icon_color or TC.ACCENT_PRIMARY
        self.setFixedHeight(100)
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 8px;
            }}
        """)
        self._setup_ui(title, value)

    def _setup_ui(self, title, value):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # 左侧：彩色图标圆（40x40）
        icon_frame = QFrame()
        icon_frame.setFixedSize(44, 44)
        icon_frame.setStyleSheet(f"""
            background-color: {self._icon_color}12;
            border-radius: 22px;
        """)
        icon_inner = QLabel("●")
        icon_inner.setAlignment(Qt.AlignCenter)
        icon_inner.setStyleSheet(
            f"color: {self._icon_color}; font-size: 20px; background: transparent;")
        icon_layout = QHBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.addWidget(icon_inner)
        layout.addWidget(icon_frame)

        # 中间：Label + Value + Subtext
        content = QVBoxLayout()
        content.setSpacing(4)

        self._label = QLabel(title)
        self._label.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: {TT.CAPTION['size']}px; "
            f"font-weight: 600; letter-spacing: 0.5px; background: transparent;")
        content.addWidget(self._label)

        self._value = QLabel(value)
        self._value.setStyleSheet(
            f"color: {TC.TEXT_PRIMARY}; font-size: {TT.TITLE_LARGE['size']}px; "
            f"font-weight: 700; background: transparent;")
        content.addWidget(self._value)

        self._sub = QLabel("")
        self._sub.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: {TT.CAPTION['size']}px; "
            f"background: transparent;")
        content.addWidget(self._sub)

        layout.addLayout(content, 1)

    def set_value(self, value, sub="", color=None):
        self._value.setText(str(value))
        if color:
            self._value.setStyleSheet(
                f"color: {color}; font-size: {TT.TITLE_LARGE['size']}px; "
                f"font-weight: 700; background: transparent;")
        if sub:
            self._sub.setText(sub)
