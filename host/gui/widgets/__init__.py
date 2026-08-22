# -*- coding: utf-8 -*-
"""
v5.5 组件库（widgets）—— 页面可复用 UI 组件。

活跃组件（生产页面使用）：
    GlassCard, StatCard, MetricTile, NodeTile, StatusPill, AlertEntry
    AlertDetail, ChartWidget
"""
from host.gui.widgets.glass_card import GlassCard                   # noqa: F401
from host.gui.widgets.stat_card import StatCard                     # noqa: F401
from host.gui.widgets.metric_tile import MetricTile                 # noqa: F401
from host.gui.widgets.node_tile import NodeTile                     # noqa: F401
from host.gui.widgets.status_pill import StatusPill                 # noqa: F401
from host.gui.widgets.alert_entry import AlertEntry                 # noqa: F401
from host.gui.widgets.alert_detail import AlertDetail               # noqa: F401
from host.gui.widgets.nav_item import NavItem                       # noqa: F401

# ChartWidget 依赖 pyqtgraph（惰性）；缺失时跳过
try:
    from host.gui.widgets.chart_widget import ChartWidget           # noqa: F401
except ImportError:
    ChartWidget = None  # type: ignore

__all__ = [
    "GlassCard", "StatCard", "MetricTile", "NodeTile", "StatusPill",
    "AlertEntry", "AlertDetail", "NavItem", "ChartWidget",
]
