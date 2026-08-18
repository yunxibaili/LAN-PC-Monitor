# -*- coding: utf-8 -*-
"""
HeaderBar —— 顶部标题栏（v5.2 Phase 4-2A）。

桌面应用标题栏，包含：当前页面标题 / 连接状态 / 通知 / 设置按钮。
纯展示组件，不访问 Store。
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.theme.spacing import ThemeSpacing as S


class HeaderBar(QWidget):
    """桌面应用顶部标题栏。"""

    settings_clicked = pyqtSignal()
    notification_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setStyleSheet(f"""
            HeaderBar {{
                background-color: {TC.BG_SURFACE};
                border-bottom: 1px solid {TC.BORDER_DEFAULT};
            }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # 左：页面标题
        self._title = QLabel("Dashboard")
        self._title.setStyleSheet(
            f"font-size: TT.TITLE_SMALL['size']px; font-weight: 600; color: {TC.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(self._title)
        layout.addStretch(1)

        # 右：连接状态
        self._conn_label = QLabel("0/0 Connected")
        self._conn_label.setStyleSheet(
            f"font-size: TT.BODY_SMALL['size']px; color: {TC.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(self._conn_label)

        layout.addSpacing(4)

        # 通知按钮
        self._notif_btn = QPushButton()
        self._notif_btn.setFixedSize(32, 32)
        self._notif_btn.setIcon(self._svg_icon(
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">'
            '<path d="M12 3a6 6 0 00-6 6c0 6-3 7-3 7h18s-3-1-3-7a6 6 0 00-6-6z"/>'
            '<path d="M10.5 21a1.5 1.5 0 003 0"/></svg>'))
        self._notif_btn.setStyleSheet(self._icon_btn_style())
        self._notif_btn.clicked.connect(self.notification_clicked.emit)
        layout.addWidget(self._notif_btn)

        # 设置按钮
        self._settings_btn = QPushButton()
        self._settings_btn.setFixedSize(32, 32)
        self._settings_btn.setIcon(self._svg_icon(
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">'
            '<circle cx="12" cy="12" r="3"/>'
            '<path d="M12 2v3M12 19v3M2 12h3M19 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1'
            'M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/></svg>'))
        self._settings_btn.setStyleSheet(self._icon_btn_style())
        self._settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self._settings_btn)

    def set_title(self, title: str) -> None:
        self._title.setText(title)

    def set_connection(self, connected: int, total: int) -> None:
        self._conn_label.setText(f"{connected}/{total} Connected")

    @staticmethod
    def _icon_btn_style() -> str:
        return f"""
            QPushButton {{
                background: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 8px;
                color: {TC.TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                background: {TC.BG_HOVER};
                color: {TC.TEXT_PRIMARY};
            }}
        """

    @staticmethod
    def _svg_icon(svg_str: str):
        """将 SVG 字符串转为 QIcon。"""
        from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
        from PyQt5.QtSvg import QSvgRenderer
        try:
            renderer = QSvgRenderer(bytearray(svg_str.encode("utf-8")))
            if renderer.isValid():
                pixmap = QPixmap(20, 20)
                pixmap.fill(QColor("transparent"))
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                return QIcon(pixmap)
        except Exception:
            pass
        return QIcon()
