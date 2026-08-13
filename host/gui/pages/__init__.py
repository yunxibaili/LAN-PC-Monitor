# -*- coding: utf-8 -*-
"""v5.2 页面模块。"""
from host.gui.pages.base_page import PageBase
from host.gui.pages.dashboard_page import DashboardPage
from host.gui.pages.nodes_page import NodesPage
from host.gui.pages.monitor_page import MonitorPage
from host.gui.pages.alerts_page import AlertsPage
from host.gui.pages.settings_page import SettingsPage

__all__ = [
    "PageBase",
    "DashboardPage", "NodesPage", "MonitorPage",
    "AlertsPage", "SettingsPage",
]
