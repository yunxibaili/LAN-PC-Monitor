# -*- coding: utf-8 -*-
"""SideNav —— Gentelella v4 暗色侧栏精确适配。"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)
from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.theme.icons import ThemeIcons
from host.gui.widgets.nav_item import NavItem
from common.i18n import tr


class SideNav(QWidget):
    page_changed = pyqtSignal(str)
    node_clicked = pyqtSignal(str)

    NAV_ITEMS = [
        ("monitor", "nav.section_monitor", [
            ("dashboard", "nav.dashboard", ThemeIcons.DASHBOARD),
            ("nodes", "nav.devices", ThemeIcons.DEVICES),
            ("monitor", "nav.monitor", ThemeIcons.MONITOR),
            ("alerts", "nav.alerts", ThemeIcons.ALERTS),
        ]),
        ("system", "nav.section_system", [
            ("history", "nav.history", ThemeIcons.HISTORY),
            ("settings", "nav.settings", ThemeIcons.SETTINGS),
        ]),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self._buttons = {}
        self._node_items = {}
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        # 背景由 paintEvent 强制填充暗色；这里只设右边框
        self.setStyleSheet(f"border-right: 1px solid {TC.SIDEBAR_BORDER};")

        # Brand area
        logo_frame = QFrame()
        logo_frame.setFixedHeight(56)
        logo_frame.setStyleSheet(f"border-bottom: 1px solid {TC.SIDEBAR_BORDER};")
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(16, 0, 16, 0)
        logo_layout.setSpacing(10)

        logo_icon = QLabel("PC")
        logo_icon.setFixedSize(28, 28)
        logo_icon.setStyleSheet(
            f"background: {TC.ACCENT_PRIMARY}; color: {TC.TEXT_ON_COLOR};"
            f" border-radius: 6px; font-size: 13px; font-weight: 700;")
        logo_icon.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_icon)

        logo_text = QLabel("PC 监控")
        logo_text.setStyleSheet(
            f"font-size: 15px; font-weight: 600; color: {TC.SIDEBAR_TEXT_ACTIVE};"
            f" background: transparent; letter-spacing: -0.2px;")
        logo_layout.addWidget(logo_text)
        root.addWidget(logo_frame)

        # Nav area
        nav_frame = QWidget()
        nav_frame.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(8, 8, 8, 8)
        nav_layout.setSpacing(1)

        for group_id, section_key, items in self.NAV_ITEMS:
            section_lbl = QLabel(tr(section_key))
            section_lbl.setStyleSheet(
                f"color: {TC.SIDEBAR_TEXT_MUTED}; font-size: 10px; font-weight: 600; "
                f"letter-spacing: 0.5px; padding: 16px 12px 4px 12px; background: transparent;")
            nav_layout.addWidget(section_lbl)
            for nav_id, i18n_key, icon_svg in items:
                item = NavItem(nav_id, tr(i18n_key), icon_svg, parent=self)
                item.clicked.connect(lambda n: self._on_nav_click(n))
                nav_layout.addWidget(item)
                self._buttons[nav_id] = item

        nav_layout.addStretch(1)
        root.addWidget(nav_frame)

        # Node section
        self._node_title = QLabel(tr("nav.connected"))
        self._node_title.setContentsMargins(20, 12, 20, 4)
        self._node_title.setStyleSheet(
            f"color: {TC.SIDEBAR_TEXT_MUTED}; font-size: {TT.CAPTION['size']}px;"
            f" font-weight: 600; background: transparent; letter-spacing: 0.5px;")
        root.addWidget(self._node_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        self._node_container = QWidget()
        self._node_layout = QVBoxLayout(self._node_container)
        self._node_layout.setContentsMargins(0, 0, 0, 0)
        self._node_layout.setSpacing(2)
        self._node_layout.addStretch(1)
        scroll.setWidget(self._node_container)
        root.addWidget(scroll, 1)

        # Bottom user section
        user_frame = QFrame()
        user_frame.setStyleSheet(f"border-top: 1px solid {TC.SIDEBAR_BORDER};")
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(12, 8, 12, 8)
        user_layout.setSpacing(10)
        avatar = QLabel("A")
        avatar.setFixedSize(32, 32)
        avatar.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 {TC.ACCENT_PRIMARY}, stop:1 {TC.ACCENT_DK});"
            f" color: {TC.TEXT_ON_COLOR}; border-radius: 16px;"
            f" font-size: 12px; font-weight: 600;")
        avatar.setAlignment(Qt.AlignCenter)
        user_layout.addWidget(avatar)
        user_info = QVBoxLayout()
        user_info.setSpacing(0)
        name_lbl = QLabel("LAN-PC-Monitor")
        name_lbl.setStyleSheet(f"color: {TC.SIDEBAR_TEXT_ACTIVE}; font-size: 12px; font-weight: 500; background: transparent;")
        user_info.addWidget(name_lbl)
        role_lbl = QLabel("v5.3.4")
        role_lbl.setStyleSheet(f"color: {TC.SIDEBAR_TEXT_MUTED}; font-size: 11px; background: transparent;")
        user_info.addWidget(role_lbl)
        user_layout.addLayout(user_info, 1)
        root.addWidget(user_frame)

        self._select("dashboard")

    def paintEvent(self, event):
        """强制填充暗色背景（不依赖 QSS 匹配）。"""
        from PyQt5.QtGui import QColor, QPainter
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(TC.SIDEBAR_BG))
        painter.end()
        super().paintEvent(event)

    def _on_nav_click(self, nav_id):
        self._select(nav_id)
        self.page_changed.emit(nav_id)

    def _select(self, nav_id):
        for nid, item in self._buttons.items():
            item.set_active(nid == nav_id)

    def add_node(self, node_id, alias):
        if node_id in self._node_items:
            return
        item = NodeItem(node_id, alias)
        item.clicked.connect(self.node_clicked.emit)
        self._node_layout.insertWidget(self._node_layout.count() - 1, item)
        self._node_items[node_id] = item

    def remove_node(self, node_id):
        item = self._node_items.pop(node_id, None)
        if item:
            self._node_layout.removeWidget(item)
            item.deleteLater()

    def update_node_status(self, node_id, status):
        item = self._node_items.get(node_id)
        if item:
            item.set_status(status)

    def navigate_to(self, nav_id):
        self._select(nav_id)
        self.page_changed.emit(nav_id)


class NodeItem(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, node_id, alias, parent=None):
        super().__init__(parent)
        self.node_id = node_id
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 5, 14, 5)
        layout.setSpacing(7)
        self._dot = QLabel("●")
        self._dot.setFixedWidth(10)
        self._dot.setStyleSheet(f"color: {TC.TEXT_DISABLED}; font-size: 8px; background: transparent;")
        layout.addWidget(self._dot)
        self._label = QLabel(alias)
        self._label.setStyleSheet(f"color: {TC.SIDEBAR_TEXT}; font-size: {TT.BODY_SMALL['size']}px; background: transparent;")
        layout.addWidget(self._label, 1)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"NodeItem:hover {{ background: {TC.SIDEBAR_HOVER}; border-radius: 4px; }}")

    def set_status(self, status):
        color = TC.STATUS_ONLINE if status in ("connected", "online") else TC.SIDEBAR_TEXT_MUTED if status in ("offline", "timeout") else TC.STATUS_WARNING
        self._dot.setStyleSheet(f"color: {color}; font-size: 8px; background: transparent;")

    def mousePressEvent(self, event):
        self.clicked.emit(self.node_id)
        super().mousePressEvent(event)
