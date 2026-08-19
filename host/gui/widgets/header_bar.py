# -*- coding: utf-8 -*-
"""HeaderBar —— Gentelella v4 topbar 精确适配。"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget
from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT


class HeaderBar(QWidget):
    settings_clicked = pyqtSignal()
    notification_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setStyleSheet(f"background-color: {TC.BG_BASE}; border-bottom: 1px solid {TC.BORDER_DEFAULT};")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        self._title = QLabel("Dashboard")
        self._title.setStyleSheet(f"font-size: {TT.TITLE_SMALL['size']}px; font-weight: 600; color: {TC.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(self._title)
        layout.addStretch(1)

        self._conn_label = QLabel("0/0 Connected")
        self._conn_label.setStyleSheet(f"font-size: {TT.BODY_SMALL['size']}px; color: {TC.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(self._conn_label)
        layout.addSpacing(4)

        self._notif_btn = QPushButton()
        self._notif_btn.setFixedSize(32, 32)
        self._notif_btn.setIcon(self._svg('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 3a6 6 0 00-6 6c0 6-3 7-3 7h18s-3-1-3-7a6 6 0 00-6-6z"/><path d="M10.5 21a1.5 1.5 0 003 0"/></svg>'))
        self._notif_btn.setStyleSheet(self._btn())
        self._notif_btn.clicked.connect(self.notification_clicked.emit)
        layout.addWidget(self._notif_btn)

        self._settings_btn = QPushButton()
        self._settings_btn.setFixedSize(32, 32)
        self._settings_btn.setIcon(self._svg('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/></svg>'))
        self._settings_btn.setStyleSheet(self._btn())
        self._settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self._settings_btn)

    def set_title(self, t): self._title.setText(t)
    def set_connection(self, c, t): self._conn_label.setText(f"{c}/{t} Connected")

    @staticmethod
    def _btn():
        return f"QPushButton {{ border:none; background:transparent; border-radius:4px; color:{TC.TEXT_SECONDARY}; width:32px; height:32px; }} QPushButton:hover {{ background:{TC.BG_BASE}; color:{TC.TEXT_PRIMARY}; }}"

    @staticmethod
    def _svg(s):
        try:
            from PyQt5.QtSvg import QSvgRenderer
            r = QSvgRenderer(bytearray(s.encode("utf-8")))
            if r.isValid():
                p = QPixmap(18,18); p.fill(QColor("transparent"))
                q = QPainter(p); r.render(q); q.end()
                return QIcon(p)
        except: pass
        return QIcon()
