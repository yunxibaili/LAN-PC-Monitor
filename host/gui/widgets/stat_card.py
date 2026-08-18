# -*- coding: utf-8 -*-
"""
StatCard —— 统计卡片组件（Gentelella 风格）。

布局：左侧彩色图标 + 中间 Label/Value/Subtext + 右侧 Spark bars
参考：Gentelella stat 组件（icon + content + spark）
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT


class StatCard(QFrame):
    """统计卡片：图标 + 标签 + 数值 + 副文本 + 可选进度条。"""

    def __init__(self, title="", value="0", icon_color=None, parent=None):
        super().__init__(parent)
        self._icon_color = icon_color or TC.ACCENT_PRIMARY
        self.setFixedHeight(90)
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
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        # 左侧：彩色图标圆
        icon_frame = QFrame()
        icon_frame.setFixedSize(40, 40)
        icon_frame.setStyleSheet(f"""
            background-color: {self._icon_color}15;
            border-radius: 20px;
        """)
        icon_inner = QLabel("●")
        icon_inner.setAlignment(Qt.AlignCenter)
        icon_inner.setStyleSheet(
            f"color: {self._icon_color}; font-size: 18px; background: transparent;")
        icon_layout = QHBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.addWidget(icon_inner)
        layout.addWidget(icon_frame)

        # 中间：Label + Value
        content = QVBoxLayout()
        content.setSpacing(2)

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
