# -*- coding: utf-8 -*-
"""NavItem —— Gentelella v4 nav-link 精确适配（图标亮色可见）。"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QFrame
from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT

# 图标颜色：暗色 sidebar 上用浅色，active 用白色
_ICON_COLOR = "#C5D0DC"       # SIDEBAR_TEXT_HOVER
_ICON_COLOR_ACTIVE = "#FFFFFF"  # SIDEBAR_TEXT_ACTIVE


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
        self._current_svg = svg
        if svg:
            self._set_svg(svg, _ICON_COLOR)
        layout.addWidget(self._icon_lbl)
        self._text_lbl = QLabel(text)
        self._text_lbl.setStyleSheet(
            f"color: {TC.SIDEBAR_TEXT}; font-size: {TT.BODY['size']}px; background: transparent;")
        layout.addWidget(self._text_lbl, 1)

    def _set_svg(self, svg_str, color=_ICON_COLOR):
        """渲染 SVG，stroke 用指定亮色（取代 currentColor）。"""
        try:
            from PyQt5.QtGui import QPixmap, QPainter, QColor
            from PyQt5.QtSvg import QSvgRenderer
            colored = svg_str.replace("currentColor", color)
            r = QSvgRenderer(bytearray(colored.encode("utf-8")))
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
        self._text_lbl.setStyleSheet(
            f"color: {color}; font-size: {TT.BODY['size']}px;"
            f" font-weight: {'500' if active else '400'}; background: transparent;")
        # 重绘图标颜色（active 白，否则浅色）
        self._set_svg(self._current_svg, _ICON_COLOR_ACTIVE if active else _ICON_COLOR)

    def set_svg_icon(self, svg_str):
        """外部更新图标。"""
        self._current_svg = svg_str
        color = _ICON_COLOR_ACTIVE if self._active else _ICON_COLOR
        self._set_svg(svg_str, color)

    def mousePressEvent(self, event):
        self.clicked.emit(self.nav_id)
        super().mousePressEvent(event)
