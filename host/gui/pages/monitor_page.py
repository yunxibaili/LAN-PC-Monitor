# -*- coding: utf-8 -*-
"""
MonitorPage —— 单节点深度监控页（v5.5 白色高密度重设计）。

节点头(StatusPill) → 指标选择(Tab) → 大图(ChartWidget) → 汇总卡(StatCard×4)。
Signal 驱动（monitor_vm.data_changed(node_id)）。
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.pages.base_page import PageBase
from host.gui.widgets.chart_widget import ChartWidget
from host.gui.widgets.glass_card import GlassCard
from host.gui.widgets.status_pill import StatusPill
from host.gui.widgets.stat_card import StatCard
from host.viewmodels.monitor_vm import METRIC_DEFS

log = logging.getLogger("host.gui.monitor_page")

_METRIC_ORDER = ["cpu", "gpu", "ram", "net_up", "net_down", "score"]


def _tab_style(active=False):
    bg = TC.ACCENT_PRIMARY if active else TC.BG_HOVER
    color = TC.TEXT_ON_COLOR if active else TC.TEXT_SECONDARY
    border = TC.ACCENT_PRIMARY if active else TC.BORDER_DEFAULT
    return f"""
        QPushButton {{
            background: {bg}; color: {color};
            border: 1px solid {border};
            border-radius: 8px; padding: 7px 16px;
            font-size: 12px; font-weight: 500;
        }}
        QPushButton:hover {{ border-color: {TC.ACCENT_PRIMARY}; }}
    """


class MonitorPage(PageBase):
    PAGE_ID = "monitor"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vm = None
        self._current_node = None
        self._current_metric = "cpu"
        self._metric_buttons = {}
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(S.XL, S.LG, S.XL, S.LG)
        root.setSpacing(S.LG)

        # 节点头
        self._header = GlassCard()
        header_l = QHBoxLayout()
        header_l.setSpacing(S.MD)
        self._icon = QLabel("🖥")
        self._icon.setStyleSheet("font-size: 18px; background: transparent;")
        header_l.addWidget(self._icon)
        self._node_lbl = QLabel("未选择节点")
        self._node_lbl.setStyleSheet(
            f"font-size: {TT.TITLE_SMALL['size']}px; font-weight: 600;"
            f" color: {TC.TEXT_PRIMARY}; background: transparent;")
        header_l.addWidget(self._node_lbl)
        self._ip_lbl = QLabel("")
        self._ip_lbl.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: {TT.BODY_SMALL['size']}px;"
            f" background: transparent;")
        header_l.addWidget(self._ip_lbl)
        header_l.addStretch(1)
        self._status = StatusPill("connecting")
        header_l.addWidget(self._status)
        self._header._layout.addLayout(header_l)
        root.addWidget(self._header)
        # 兼容旧接口
        self._title = self._node_lbl
        self._info_label = self._ip_lbl

        # 指标 Tab
        self._tabs = GlassCard()
        tabs_l = QHBoxLayout()
        tabs_l.setSpacing(S.XS)
        tabs_l.setContentsMargins(0, 0, 0, 0)
        for key in _METRIC_ORDER:
            info = METRIC_DEFS.get(key, {})
            btn = QPushButton(info.get("label", key.upper()))
            btn.setCheckable(True)
            btn.setChecked(key == "cpu")
            btn.setStyleSheet(_tab_style(active=(key == "cpu")))
            btn.clicked.connect(lambda checked, k=key: self._on_metric_clicked(k))
            tabs_l.addWidget(btn)
            self._metric_buttons[key] = btn
        tabs_l.addStretch(1)
        self._tabs._layout.addLayout(tabs_l)
        root.addWidget(self._tabs)

        # 图表面板
        self._panel = GlassCard()
        chart_title = QLabel("CPU 使用率")
        chart_title.setStyleSheet(
            f"font-size: {TT.TITLE_SMALL['size']}px; font-weight: 600;"
            f" color: {TC.TEXT_PRIMARY}; background: transparent;")
        self._chart_title = chart_title
        self._panel._layout.addWidget(chart_title)
        self._chart = ChartWidget(title="", y_range=(0, 100))
        self._chart.setMinimumHeight(280)
        self._panel._layout.addWidget(self._chart, 1)
        root.addWidget(self._panel, 1)

        # 汇总卡
        summary = QHBoxLayout()
        summary.setSpacing(S.MD)
        self._cur = StatCard("当前", "—", TC.ACCENT_PRIMARY, sub="实时值")
        self._avg = StatCard("平均", "—", TC.ACCENT_PRIMARY, sub="区间均值")
        self._peak = StatCard("峰值", "—", TC.STATUS_WARNING, sub="区间最大")
        self._status_card = StatCard("状态", "—", TC.STATUS_ONLINE)
        for c in (self._cur, self._avg, self._peak, self._status_card):
            summary.addWidget(c, 1)
        root.addLayout(summary)

        # 兼容旧接口（monitor_redesign 测试引用）
        self._selector = self._tabs
        self._chart_panel = self._panel
        self._chart_panel._current_card = self._cur
        self._chart_panel._avg_card = self._avg
        self._chart_panel._peak_card = self._peak
        self._chart_panel._status_card = self._status_card
        self._header._node_lbl = self._node_lbl
        self._header._subtitle_lbl = self._ip_lbl
        self._header.set_node = lambda node_id, alias="", status="connected": (
            self._node_lbl.setText(alias or node_id),
            self._status.set_status(status))
        self._header.clear = lambda: (self._node_lbl.setText("未选择节点"), self._status.set_status("connecting"))

    # ---- VM ----
    def set_view_model(self, vm):
        self._vm = vm
        if vm:
            vm.data_changed.connect(self._on_data_changed)

    def on_show(self):
        super().on_show()
        self._refresh_chart()

    def on_hide(self):
        if self._vm:
            try:
                self._vm.data_changed.disconnect(self._on_data_changed)
            except (TypeError, RuntimeError):
                pass
        super().on_hide()

    # ---- 节点/指标选择 ----
    def set_node(self, node_id):
        self._current_node = node_id
        alias = ""
        if self._vm:
            summary = self._vm.get_summary(node_id)
            alias = summary.get("alias", "")
        self._node_lbl.setText(alias or node_id)
        self._ip_lbl.setText(f"{node_id} · 实时监控")
        self._status.set_status("connected")
        self._refresh_chart()

    def get_node(self):
        return self._current_node

    def _on_metric_clicked(self, metric):
        self._current_metric = metric
        for k, btn in self._metric_buttons.items():
            btn.setChecked(k == metric)
            btn.setStyleSheet(_tab_style(active=(k == metric)))
        self._refresh_chart()

    def _on_data_changed(self, node_id):
        if node_id == self._current_node:
            self._refresh_chart()

    def _refresh_chart(self):
        if not self._vm or not self._current_node:
            self._chart.reset()
            for c in (self._cur, self._avg, self._peak, self._status_card):
                c.set_value("—")
            return
        metric = self._current_metric
        info = METRIC_DEFS.get(metric, {})
        points = self._vm.get_history(self._current_node, metric)
        # 图表标题（仅更新文本，不重建控件）
        self._chart_title.setText(info.get("label", metric.upper()))
        self._chart._title = info.get("label", metric.upper())
        # 图表范围
        yr = info.get("y_range")
        if yr:
            self._chart.setYRange(yr[0], yr[1], padding=0)
        if not points:
            self._chart.reset()
            for c in (self._cur, self._avg, self._peak, self._status_card):
                c.set_value("—")
            return
        self._chart.set_series(points, color=TC.CHART_PRIMARY)
        # 汇总
        values = [p.value for p in points]
        unit = info.get("unit", "%")
        cur_v = values[-1]
        avg_v = sum(values) / len(values)
        peak_v = max(values)
        self._cur.set_value(f"{cur_v:.1f}{unit}")
        self._avg.set_value(f"{avg_v:.1f}{unit}")
        self._peak.set_value(f"{peak_v:.1f}{unit}", color=TC.STATUS_WARNING)
        status, col = self._judge(peak_v)
        self._status_card.set_value(status, color=col)

    def _judge(self, peak):
        if peak >= 95:
            return "CRITICAL", TC.DANGER
        if peak >= 80:
            return "WARNING", TC.WARNING
        return "NORMAL", TC.STATUS_ONLINE
