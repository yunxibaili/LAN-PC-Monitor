# -*- coding: utf-8 -*-
"""
NavItem —— 侧边栏导航项（Gentelella v4 精确适配）。

CSS 来源：gentelella-master/src/scss/v4/_layout.scss
.nav-link / .nav-link:hover / .nav-link.active
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QFrame

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT


class NavItem(QFrame):
    """侧栏导航项：图标 + 文字，点击切换。"""
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

        # 图标
        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(18, 18)
        self._icon_lbl.setStyleSheet("background: transparent;")
        if svg:
            self._set_svg(svg)
        layout.addWidget(self._icon_lbl)

        # 文字
        self._text_lbl = QLabel(text)
        self._text_lbl.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: {TT.BODY['size']}px;"
            f" background: transparent;")
        layout.addWidget(self._text_lbl, 1)

    def _set_svg(self, svg_str: str):
        try:
            from PyQt5.QtGui import QPixmap, QPainter, QColor
            from PyQt5.QtSvg import QSvgRenderer
            renderer = QSvgRenderer(bytearray(svg_str.encode("utf-8")))
            if renderer.isValid():
                pixmap = QPixmap(18, 18)
                pixmap.fill(QColor("transparent"))
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                self._icon_lbl.setPixmap(pixmap)
        except Exception:
            pass

    def _style(self, active: bool) -> str:
        if active:
            return f"""
                NavItem {{
                    background: {TC.SIDEBAR_ACTIVE_BG};
                    border-radius: 4px;
                }}
            """
        return f"""
            NavItem {{
                background: transparent;
                border-radius: 4px;
            }}
            NavItem:hover {{
                background: {TC.SIDEBAR_HOVER};
            }}
        """

    def set_active(self, active: bool):
        self._active = active
        self.setStyleSheet(self._style(active))
        if active:
            self._text_lbl.setStyleSheet(
                f"color: {TC.SIDEBAR_TEXT_ACTIVE}; font-size: {TT.BODY['size']}px;"
                f" font-weight: 500; background: transparent;")
        else:
            self._text_lbl.setStyleSheet(
                f"color: {TC.SIDEBAR_TEXT}; font-size: {TT.BODY['size']}px;"
                f" background: transparent;")

    def mousePressEvent(self, event):
        self.clicked.emit(self.nav_id)
        super().mousePressEvent(event)
