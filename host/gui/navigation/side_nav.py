# -*- coding: utf-8 -*-
"""
SideNav —— 左侧导航栏（v5.2 Phase 4-2A）。

宽度 220px，桌面应用风格：
- Logo + 版本
- 导航菜单（蓝色高亮当前页）
- 底部节点列表（带状态圆点）
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.theme.icons import ThemeIcons
from host.gui.widgets.nav_item import NavItem
from common.i18n import tr


class NavButton(QPushButton):
    """导航项按钮（Gentelella 风格）。"""

    def __init__(self, text="", icon="", parent=None):
        super().__init__(parent)
        display = f"  {icon}  {text}" if icon else f"    {text}"
        self.setText(display)
        self.setCheckable(True)
        self.setFixedHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left; padding: 0 16px; border: none;
                border-left: 3px solid transparent;
                background: transparent; color: {TC.TEXT_SECONDARY}; font-size: TT.BODY['size']px;
                border-radius: 0 6px 6px 0;
            }}
            QPushButton:hover {{
                background: {TC.BG_HOVER};
                color: {TC.TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                border-left: 3px solid {TC.ACCENT_PRIMARY};
                background: rgba(59,130,246,0.08);
                color: {TC.TEXT_PRIMARY}; font-weight: 600;
            }}
        """)


class NodeItem(QFrame):
    """侧栏节点快速列表项。"""
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
        self._label.setStyleSheet(f"color: {TC.TEXT_PRIMARY}; font-size: TT.BODY_SMALL['size']px; background: transparent;")
        layout.addWidget(self._label, 1)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"NodeItem:hover {{ background: {TC.BG_HOVER}; border-radius: 6px; }}")

    def set_status(self, status):
        color = TC.status_color(status)
        self._dot.setStyleSheet(f"color: {color}; font-size: 8px; background: transparent;")

    def mousePressEvent(self, event):
        self.clicked.emit(self.node_id)
        super().mousePressEvent(event)


class SideNav(QWidget):
    """侧边导航栏（220px）。"""

    page_changed = pyqtSignal(str)
    node_clicked = pyqtSignal(str)

    NAV_ITEMS = [
        ("monitor", "nav.section_monitor", [
            ("dashboard", "nav.dashboard", ThemeIcons.DASHBOARD),
            ("nodes",     "nav.devices",   ThemeIcons.DEVICES),
            ("monitor",   "nav.monitor",   ThemeIcons.MONITOR),
            ("alerts",    "nav.alerts",    ThemeIcons.ALERTS),
        ]),
        ("system", "nav.section_system", [
            ("history",   "nav.history",   ThemeIcons.HISTORY),
            ("settings",  "nav.settings",  ThemeIcons.SETTINGS),
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
        self.setStyleSheet(f"background: {TC.BG_SURFACE}; border-right: 1px solid {TC.BORDER_SUBTLE};")

        # Logo
        logo_frame = QFrame()
        logo_frame.setFixedHeight(56)
        logo_frame.setStyleSheet(f"background: {TC.BG_SURFACE}; border-bottom: 1px solid {TC.BORDER_DEFAULT};")
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(14, 0, 14, 0)
        logo_icon = QLabel("PC")
        logo_icon.setFixedSize(28, 28)
        logo_icon.setStyleSheet(
            f"background: {TC.ACCENT_PRIMARY}; color: {TC.TEXT_ON_COLOR}; border-radius: 6px;"
            f" font-size: 11px; font-weight: 700;")
        logo_icon.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_icon)
        logo_text = QLabel("PC 监控")
        logo_text.setStyleSheet(f"font-size: TT.BODY['size']px; font-weight: 700; color: {TC.ACCENT_PRIMARY}; background: transparent;")
        logo_layout.addWidget(logo_text)
        root.addWidget(logo_frame)

        # Nav buttons with section headers
        nav_frame = QWidget()
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(8, 8, 8, 8)
        nav_layout.setSpacing(2)

        for group_id, section_key, items in self.NAV_ITEMS:
            # Section header
            section_lbl = QLabel(tr(section_key))
            section_lbl.setStyleSheet(
                f"color: {TC.TEXT_DISABLED}; font-size: {TT.CAPTION['size']}px; font-weight: 600; "
                f"letter-spacing: 1px; padding: 12px 8px 4px 8px; background: transparent;")
            nav_layout.addWidget(section_lbl)

            for nav_id, i18n_key, icon_svg in items:
                item = NavItem(nav_id, tr(i18n_key), icon_svg, parent=self)
                item.clicked.connect(lambda n: self._on_nav_click(n))
                nav_layout.addWidget(item)
                self._buttons[nav_id] = item

        nav_layout.addStretch(1)
        root.addWidget(nav_frame)

        # Node section（无硬分隔线，用间距自然分隔）
        self._node_title = QLabel(tr("nav.connected"))
        self._node_title.setContentsMargins(14, 12, 14, 4)
        self._node_title.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: {TT.CAPTION['size']}px;"
            f" font-weight: 600; background: transparent; letter-spacing: 1px;")
        root.addWidget(self._node_title)

        # Node list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"background: transparent; border: none;")
        self._node_container = QWidget()
        self._node_layout = QVBoxLayout(self._node_container)
        self._node_layout.setContentsMargins(0, 0, 0, 0)
        self._node_layout.setSpacing(2)
        self._node_layout.addStretch(1)
        scroll.setWidget(self._node_container)
        root.addWidget(scroll, 1)

        self._select("dashboard")

    def _on_nav_click(self, nav_id):
        self._select(nav_id)
        self.page_changed.emit(nav_id)

    def _select(self, nav_id):
        for nid, item in self._buttons.items():
            if hasattr(item, 'set_active'):
                item.set_active(nid == nav_id)
            elif hasattr(item, 'setChecked'):
                item.setChecked(nid == nav_id)

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

    def update_node_title(self, online, total):
        self._node_title.setText(f"ONLINE NODES ({online}/{total})")
