# -*- coding: utf-8 -*-
"""
NavigationController —— 页面切换控制（v5.2 Phase 3-8）。

职责：
  - SideNav ↔ contentStack 页面切换
  - 页面生命周期 on_show/on_hide
  - 侧栏节点点击 -> Monitor 页

不访问 Store / 业务逻辑；只做 UI 路由。
"""
import logging

from PyQt5.QtWidgets import QStackedWidget

from host.gui.navigation.side_nav import SideNav

log = logging.getLogger("host.gui.controllers.navigation")

# 侧栏标题映射
_PAGE_TITLES = {
    "dashboard": "总览", "nodes": "节点管理",
    "monitor": "监控", "alerts": "告警中心", "settings": "设置",
}


class NavigationController:
    """页面导航控制器。"""

    def __init__(self, side_nav: SideNav, content_stack: QStackedWidget,
                 pages: dict, legacy_widget=None):
        """
        :param side_nav:      SideNav 实例
        :param content_stack: 内容 QStackedWidget
        :param pages:         {page_id: PageBase}
        :param legacy_widget: 可选，旧 UI widget（若无则 None）
        """
        self.side_nav = side_nav
        self.content_stack = content_stack
        self.pages = pages
        self._legacy = legacy_widget
        self._header_title = None
        self._on_monitor_node = None   # 回调：node_id -> Monitor 页

    # ---------- 连接 ----------

    def connect_signals(self, header_title=None,
                        on_monitor_node=None) -> None:
        """连接 SideNav 信号。"""
        self._header_title = header_title
        self._on_monitor_node = on_monitor_node
        self.side_nav.page_changed.connect(self.navigate)
        if on_monitor_node:
            self.side_nav.node_clicked.connect(on_monitor_node)

    # ---------- 导航 ----------

    def navigate(self, page_id: str) -> None:
        """切换到指定页面。"""
        if page_id == "nodes" and self._legacy is not None:
            # 兼容：nodes 映射到 legacy（若保留）
            self._switch_to_widget(self._legacy)
            self._update_title(page_id)
            return
        page = self.pages.get(page_id)
        if page is None:
            return
        self._switch_to_widget(page)
        self._update_title(page_id)

    def navigate_to_node(self, node_id: str) -> None:
        """侧栏节点点击 -> Monitor 页。"""
        page = self.pages.get("monitor")
        if page is None:
            return
        if hasattr(page, "set_node"):
            page.set_node(node_id)
        self._switch_to_widget(page)
        self.side_nav._select("monitor")
        self._update_title("monitor")

    def select(self, page_id: str) -> None:
        """程序化选中侧栏项并导航。"""
        self.side_nav._select(page_id)
        self.navigate(page_id)

    # ---------- 内部 ----------

    def _switch_to_widget(self, widget) -> None:
        current = self.content_stack.currentWidget()
        if current is not None and hasattr(current, "on_hide"):
            current.on_hide()
        idx = self.content_stack.indexOf(widget)
        if idx >= 0:
            self.content_stack.setCurrentIndex(idx)
        if hasattr(widget, "on_show"):
            widget.on_show()

    def _update_title(self, page_id: str) -> None:
        if self._header_title is not None:
            self._header_title.setText(_PAGE_TITLES.get(page_id, ""))
