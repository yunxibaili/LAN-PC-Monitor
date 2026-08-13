# -*- coding: utf-8 -*-
"""
AppCard —— 统一 SaaS 卡片组件（v5.2 Phase 4-1B）。

所有卡片的基类/容器：
- 圆角 12px
- 深色背景
- hover 提升 + 边框高亮
- padding 统一 16px
- 点击信号
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QVBoxLayout

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.theme.layout import ThemeLayout as L


class AppCard(QFrame):
    """SaaS 风格卡片容器。"""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(S.LG, S.MD, S.LG, S.MD)
        self._layout.setSpacing(S.SM)

    def _apply_style(self):
        self.setStyleSheet(f"""
            AppCard {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: {L.CARD_RADIUS if hasattr(L, 'CARD_RADIUS') else 12}px;
            }}
            AppCard:hover {{
                border-color: {TC.ACCENT_PRIMARY};
                background-color: {TC.BG_ELEVATED};
            }}
        """)

    def addWidget(self, widget):
        self._layout.addWidget(widget)

    def addLayout(self, layout):
        self._layout.addLayout(layout)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)
