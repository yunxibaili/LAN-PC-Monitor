# -*- coding: utf-8 -*-
"""SectionTitle —— 区块标题（v5.2 Phase 4-2）。"""
from PyQt5.QtWidgets import QLabel

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.metrics import ThemeMetrics as TM


class SectionTitle(QLabel):
    """区块标题：大号文字 + 底部分隔线。"""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            font-size: {TM.FONT_SIZE_XL}px; font-weight: bold;
            color: {TC.TEXT_PRIMARY}; padding: {TM.SPACING_MD}px 0;
            border-bottom: 1px solid {ThemeColors.BORDER_DEFAULT};
        """)
