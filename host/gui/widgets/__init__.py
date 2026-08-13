# -*- coding: utf-8 -*-
"""
v5.2 组件库（widgets）—— 页面可复用 UI 组件。

活跃组件（页面使用）：
    NodeCard, ResourceCard, ChartWidget, ChartPanel
    NodeExplorer, DetailDashboard, MonitorHeader, MetricSelector
    HeaderBar, DetailPanel, NodeListWidget

保留组件（测试引用，待后续清理）：
    StatusBadge, QualityBadge, EmptyState, PageHeader, MetricBar

归档组件（已移至 archive/）：
    CardWidget, AppCard, MetricCard, SectionTitle
"""
from host.gui.widgets.node_card import NodeCard                   # noqa: F401
from host.gui.widgets.resource_card import ResourceCard             # noqa: F401
from host.gui.widgets.chart_panel import ChartPanel                 # noqa: F401
from host.gui.widgets.node_explorer import NodeExplorer             # noqa: F401
from host.gui.widgets.detail_dashboard import DetailDashboard       # noqa: F401
from host.gui.widgets.monitor_header import MonitorHeader           # noqa: F401
from host.gui.widgets.metric_selector import MetricSelector         # noqa: F401
from host.gui.widgets.header_bar import HeaderBar                   # noqa: F401
from host.gui.widgets.detail_panel import DetailPanel               # noqa: F401
from host.gui.widgets.node_list import NodeListWidget               # noqa: F401

# 保留组件（测试引用）
from host.gui.widgets.status_badge import StatusBadge               # noqa: F401
from host.gui.widgets.quality_badge import QualityBadge             # noqa: F401
from host.gui.widgets.empty_state import EmptyState                 # noqa: F401
from host.gui.widgets.page_header import PageHeader                 # noqa: F401
from host.gui.widgets.metric_bar import MetricBar                   # noqa: F401

# ChartWidget 依赖 pyqtgraph（惰性）；缺失时跳过
try:
    from host.gui.widgets.chart_widget import ChartWidget           # noqa: F401
except ImportError:
    ChartWidget = None  # type: ignore

__all__ = [
    "NodeCard", "ResourceCard", "ChartWidget", "ChartPanel",
    "NodeExplorer", "DetailDashboard", "MonitorHeader", "MetricSelector",
    "HeaderBar", "DetailPanel", "NodeListWidget",
    "StatusBadge", "QualityBadge", "EmptyState", "PageHeader", "MetricBar",
]
