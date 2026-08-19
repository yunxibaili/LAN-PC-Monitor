# -*- coding: utf-8 -*-
"""NavItem —— Gentelella v4 nav-link 精确适配。"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QFrame
from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT


class NavItem(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, nav_id: str, text: str, svg: str = "", parent=None):
        super().__init__(parent)
        self.nav_id = nav_id
        self._active = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(32)
        self.setStyleSheet(self._style(False))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)
        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(18, 18)
        self._icon_lbl.setStyleSheet("background: transparent;")
        if svg:
            self._set_svg(svg)
        layout.addWidget(self._icon_lbl)
        self._text_lbl = QLabel(text)
        self._text_lbl.setStyleSheet(
            f"color: {TC.SIDEBAR_TEXT}; font-size: {TT.BODY['size']}px; background: transparent;")
        layout.addWidget(self._text_lbl, 1)

    def _set_svg(self, svg_str):
        try:
            from PyQt5.QtGui import QPixmap, QPainter, QColor
            from PyQt5.QtSvg import QSvgRenderer
            r = QSvgRenderer(bytearray(svg_str.encode("utf-8")))
            if r.isValid():
                p = QPixmap(18, 18); p.fill(QColor("transparent"))
                q = QPainter(p); r.render(q); q.end()
                self._icon_lbl.setPixmap(p)
        except Exception:
            pass

    def _style(self, active):
        if active:
            return f"NavItem {{ background: {TC.SIDEBAR_ACTIVE_BG}; border-radius: 4px; }}"
        return f"NavItem {{ background: transparent; border-radius: 4px; }} NavItem:hover {{ background: {TC.SIDEBAR_HOVER}; }}"

    def set_active(self, active):
        self._active = active
        self.setStyleSheet(self._style(active))
        color = TC.SIDEBAR_TEXT_ACTIVE if active else TC.SIDEBAR_TEXT
        self._text_lbl.setStyleSheet(f"color: {color}; font-size: {TT.BODY['size']}px; font-weight: {'500' if active else '400'}; background: transparent;")

    def mousePressEvent(self, event):
        self.clicked.emit(self.nav_id)
        super().mousePressEvent(event)
