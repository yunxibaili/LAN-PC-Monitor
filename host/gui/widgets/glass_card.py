# -*- coding: utf-8 -*-
"""
GlassCard —— 白色高密度卡片基座（v5.5 重设计）。

遵循 Apple/Emil 设计原则：
  - 半透明柔影（SHADOW_MD）代替实线硬边框
  - 顶部 1px 高光渐变（材质层次）
  - 可选：悬停升阶（BG_ELEVATED）与按压反馈（scale 0.97）

纯 UI 组件，只 import Theme。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QVBoxLayout

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.metrics import ThemeMetrics as TM
from host.gui.theme.spacing import ThemeSpacing as S


class GlassCard(QFrame):
    """卡片基座：白底 + 柔影 + 圆角（可选 hover 升阶 + 按压反馈）。"""

    def __init__(self, parent=None, hover=False, clickable=False):
        super().__init__(parent)
        self._hover = hover
        self._clickable = clickable
        self.setObjectName("glassCard")
        if clickable:
            self.setCursor(Qt.PointingHandCursor)
        self._apply_style()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(S.MD, S.MD, S.MD, S.MD)
        self._layout.setSpacing(S.SM)

    def _apply_style(self, elevated=False):
        bg = TC.BG_ELEVATED if elevated else TC.BG_CARD
        border = TC.BORDER_DEFAULT if not elevated else TC.BORDER_FOCUS
        self.setStyleSheet(f"""
            QFrame#glassCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: {TM.RADIUS_LG}px;
            }}
        """)

    def enterEvent(self, event):
        if self._hover:
            self._apply_style(elevated=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._hover:
            self._apply_style(elevated=False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        # 按压反馈：轻微缩放（Apple 按压 scale 原则）
        if self._clickable:
            self.setStyleSheet(self._style("scale(0.98)"))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._clickable:
            self._apply_style(elevated=self._hover)
        super().mouseReleaseEvent(event)

    def _style(self, transform):
        return f"""
            QFrame#glassCard {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: {TM.RADIUS_LG}px;
            }}
        """
