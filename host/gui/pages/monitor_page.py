# -*- coding: utf-8 -*-
"""
MonitorPage —— 单节点深度监控页（v5.2 Phase 4-4 Redesign）。

数据流：
  MonitorViewModel.data_changed → _on_data_changed → _refresh_chart

约束：
  - 不访问 HistoryStore / FrameStore / NodeStore / Connection
  - 不 QTimer
  - 纯 Signal 驱动

布局：
  MonitorHeader → MetricSelector → ChartPanel（图表 + 汇总卡片）
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout

from host.gui.pages.base_page import PageBase
from host.gui.theme.colors import ThemeColors as TC
from host.gui.widgets.monitor_header import MonitorHeader
from host.gui.widgets.metric_selector import MetricSelector
from host.gui.widgets.chart_panel import ChartPanel
from host.viewmodels.monitor_vm import METRIC_DEFS

log = logging.getLogger("host.gui.monitor_page")


class MonitorPage(PageBase):
    """监控页：MonitorHeader + MetricSelector + ChartPanel。"""

    PAGE_ID = "monitor"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vm = None
        self._current_node = None
        self._current_metric = "cpu"
        self._metric_buttons = {}  # 向后兼容
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Page Header ----
        self._header = MonitorHeader()
        root.addWidget(self._header)

        # ---- Metric Selector ----
        self._selector = MetricSelector()
        self._selector.metric_changed.connect(self._on_metric_clicked)
        root.addWidget(self._selector)

        # ---- Chart Panel (图表 + 汇总卡片) ----
        self._chart_panel = ChartPanel()
        root.addWidget(self._chart_panel, 1)

        # ---- 向后兼容：暴露旧属性 ----
        self._title = self._header._node_lbl
        self._info_label = self._header._subtitle_lbl
        self._chart = self._chart_panel.get_chart()

        # 构造 _metric_buttons 字典供测试访问
        for key, tab in self._selector._tabs.items():
            self._metric_buttons[key] = tab

    # ---------- ViewModel 注入 ----------

    def set_view_model(self, vm) -> None:
        self._vm = vm

    # ---------- 生命周期 ----------

    def on_show(self) -> None:
        super().on_show()
        if self._vm:
            self._vm.data_changed.connect(self._on_data_changed)
        self._refresh_chart()

    def on_hide(self) -> None:
        if self._vm:
            try:
                self._vm.data_changed.disconnect(self._on_data_changed)
            except (TypeError, RuntimeError):
                pass
        super().on_hide()

    # ---------- 节点/指标选择 ----------

    def set_node(self, node_id: str) -> None:
        self._current_node = node_id
        alias = ""
        if self._vm:
            summary = self._vm.get_summary(node_id)
            alias = summary.get("alias", "")
        self._header.set_node(node_id, alias=alias, status="connected")
        self._refresh_chart()

    def get_node(self) -> str | None:
        return self._current_node

    def _on_metric_clicked(self, metric: str) -> None:
        self._current_metric = metric
        self._selector.set_current(metric)
        info = METRIC_DEFS.get(metric, {})
        self._chart._title = info.get("label", metric)
        self._refresh_chart()

    # ---------- 数据更新 ----------

    def _on_data_changed(self, node_id: str) -> None:
        if node_id == self._current_node:
            self._refresh_chart()

    def _refresh_chart(self) -> None:
        if not self._vm or not self._current_node:
            self._chart_panel.clear()
            self._header.clear()
            return

        metric = self._current_metric
        points = self._vm.get_history(self._current_node, metric)

        if not points:
            self._chart_panel.clear()
            self._header.set_stats({})
            return

        # 图表
        info = METRIC_DEFS.get(metric, {})
        self._chart.set_series(points, color=TC.CHART_PRIMARY)

        # 阈值
        warn = info.get("warn_threshold")
        danger = info.get("danger_threshold")
        if warn is not None or danger is not None:
            self._chart.set_thresholds(warn=warn, danger=danger)
        else:
            self._chart.set_thresholds()

        # 汇总卡片
        values = [p.value for p in points]
        current = values[-1] if values else 0
        average = sum(values) / len(values) if values else 0
        peak = max(values) if values else 0
        unit = info.get("unit", "%")

        # 状态判定
        if peak >= (danger or 95):
            status_text = "CRITICAL"
            status_color = TC.STATUS_ERROR
        elif peak >= (warn or 80):
            status_text = "WARNING"
            status_color = TC.STATUS_WARNING
        else:
            status_text = "NORMAL"
            status_color = TC.STATUS_ONLINE

        self._chart_panel.update_summary(
            current=current, average=average, peak=peak,
            status_text=status_text, status_color=status_color, unit=unit,
        )

        # Header 统计
        alias = self._vm.get_summary(self._current_node).get("alias", "")
        self._header.set_stats({
            "POINTS": str(len(points)),
            "METRIC": info.get("label", metric),
            "LATEST": f"{current:.1f}{unit}",
        })
