# -*- coding: utf-8 -*-
"""CardWidget —— 通用卡片容器（v5.2 Phase 4-2）。"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QVBoxLayout

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.metrics import ThemeMetrics as TM


class CardWidget(QFrame):
    """通用卡片容器：圆角 + 背景 + 阴影。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            CardWidget {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: {TM.RADIUS_LG}px;
            }}
            CardWidget:hover {{
                border-color: {TC.PRIMARY};
            }}
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(
            TM.SPACING_LG, TM.SPACING_MD, TM.SPACING_LG, TM.SPACING_MD)
        self._layout.setSpacing(TM.SPACING_SM)

    def addWidget(self, widget):
        self._layout.addWidget(widget)

    def addLayout(self, layout):
        self._layout.addLayout(layout)
