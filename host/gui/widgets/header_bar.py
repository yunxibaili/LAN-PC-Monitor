# -*- coding: utf-8 -*-
"""
HeaderBar —— 顶部标题栏（Gentelella v4 topbar 精确适配）。

CSS 来源：gentelella-master/src/scss/v4/_layout.scss
.topbar / .tb-btn
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.theme.spacing import ThemeSpacing as S


class HeaderBar(QWidget):
    """桌面应用顶部标题栏（Gentelella topbar 风格）。"""

    settings_clicked = pyqtSignal()
    notification_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        # Gentelella topbar: bg white, border-bottom, padding 0 24px
        self.setStyleSheet(f"""
            HeaderBar {{
                background-color: {TC.BG_BASE};
                border-bottom: 1px solid {TC.BORDER_DEFAULT};
            }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        # 左：页面标题
        self._title = QLabel("Dashboard")
        self._title.setStyleSheet(
            f"font-size: {TT.TITLE_SMALL['size']}px; font-weight: 600;"
            f" color: {TC.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(self._title)
        layout.addStretch(1)

        # 右：连接状态
        self._conn_label = QLabel("0/0 Connected")
        self._conn_label.setStyleSheet(
            f"font-size: {TT.BODY_SMALL['size']}px; color: {TC.TEXT_SECONDARY};"
            f" background: transparent;")
        layout.addWidget(self._conn_label)

        layout.addSpacing(4)

        # 通知按钮 (Gentelella .tb-btn: 32x32, radius 4px, transparent)
        self._notif_btn = QPushButton()
        self._notif_btn.setFixedSize(32, 32)
        self._notif_btn.setIcon(self._svg_icon(
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">'
            '<path d="M12 3a6 6 0 00-6 6c0 6-3 7-3 7h18s-3-1-3-7a6 6 0 00-6-6z"/>'
            '<path d="M10.5 21a1.5 1.5 0 003 0"/></svg>'))
        self._notif_btn.setStyleSheet(self._tb_btn_style())
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
        self._settings_btn.setStyleSheet(self._tb_btn_style())
        self._settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self._settings_btn)

    def set_title(self, title: str) -> None:
        self._title.setText(title)

    def set_notification_count(self, count: int) -> None:
        """设置通知计数徽章。"""
        if count > 0:
            self._notif_btn.setText(str(count))
            self._notif_btn.setStyleSheet(f"""
                QPushButton {{
                    width: 32px; height: 32px;
                    border: none; background: {TC.DANGER};
                    border-radius: 4px; color: {TC.TEXT_ON_COLOR};
                    font-size: 10px; font-weight: 700;
                }}
            """)
        else:
            self._notif_btn.setText("")
            self._notif_btn.setStyleSheet(self._tb_btn_style())
        self._title.setText(title)

    def set_connection(self, connected: int, total: int) -> None:
        self._conn_label.setText(f"{connected}/{total} Connected")

    @staticmethod
    def _tb_btn_style() -> str:
        # Gentelella .tb-btn: 32x32, no border, transparent bg, radius 4px
        return f"""
            QPushButton {{
                width: 32px; height: 32px;
                border: none; background: transparent;
                border-radius: 4px;
                color: {TC.TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                background: {TC.BG_BASE};
                color: {TC.TEXT_PRIMARY};
            }}
        """

    @staticmethod
    def _svg_icon(svg_str: str):
        from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
        from PyQt5.QtSvg import QSvgRenderer
        try:
            renderer = QSvgRenderer(bytearray(svg_str.encode("utf-8")))
            if renderer.isValid():
                pixmap = QPixmap(18, 18)
                pixmap.fill(QColor("transparent"))
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                return QIcon(pixmap)
        except Exception:
            pass
        return QIcon()
