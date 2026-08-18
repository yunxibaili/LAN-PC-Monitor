# -*- coding: utf-8 -*-
"""
NavItem —— 侧边栏导航项（Gentelella 风格，SVG 图标 + 文字）。

替代 QPushButton，支持 inline SVG 渲染。
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QFrame

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT

# SVG 渲染：Qt5Svg 可选依赖
try:
    from PyQt5.QtGui import QPixmap, QPainter, QColor
    from PyQt5.QtSvg import QSvgRenderer
    _HAS_SVG = True
except ImportError:
    _HAS_SVG = False


class NavItem(QFrame):
    """侧栏导航项：SVG 图标 + 文字，点击切换。"""
    clicked = pyqtSignal(str)

    def __init__(self, nav_id: str, text: str, svg: str = "", parent=None):
        super().__init__(parent)
        self.nav_id = nav_id
        self._active = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(36)
        self.setStyleSheet(self._base_style(False))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 16, 0)
        layout.setSpacing(10)

        # SVG 图标（16x16）
        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(18, 18)
        self._icon_lbl.setStyleSheet("background: transparent;")
        if svg:
            self._set_svg(svg)
        layout.addWidget(self._icon_lbl)

        # 文字
        self._text_lbl = QLabel(text)
        self._text_lbl.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: {TT.BODY['size']}px; background: transparent;")
        layout.addWidget(self._text_lbl, 1)

    def _set_svg(self, svg_str: str):
        """将 SVG 字符串渲染为 QPixmap（Qt5Svg 可选）。"""
        if not _HAS_SVG:
            return
        try:
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

    def _base_style(self, active: bool) -> str:
        if active:
            return f"""
                NavItem {{
                    border-left: 3px solid {TC.ACCENT_PRIMARY};
                    background: rgba(59,130,246,0.08);
                    border-radius: 0 6px 6px 0;
                }}
            """
        return f"""
            NavItem {{
                border-left: 3px solid transparent;
                background: transparent;
                border-radius: 0 6px 6px 0;
                margin-left: 0px;
            }}
            NavItem:hover {{
                background: {TC.BG_HOVER};
            }}
        """

    def set_active(self, active: bool):
        self._active = active
        self.setStyleSheet(self._base_style(active))
        if active:
            self._text_lbl.setStyleSheet(
                f"color: {TC.TEXT_PRIMARY}; font-size: {TT.BODY['size']}px; font-weight: 600; background: transparent;")
        else:
            self._text_lbl.setStyleSheet(
                f"color: {TC.TEXT_SECONDARY}; font-size: {TT.BODY['size']}px; background: transparent;")

    def mousePressEvent(self, event):
        self.clicked.emit(self.nav_id)
        super().mousePressEvent(event)
