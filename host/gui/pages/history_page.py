# -*- coding: utf-8 -*-
"""
HistoryPage —— 历史趋势页（v5.5 白色高密度重设计）。

节点选择 → 时间范围按钮 → 指标勾选 → 多曲线图 → 汇总卡。
Signal 驱动（history_vm.data_changed）。
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.pages.base_page import PageBase
from host.gui.widgets.chart_widget import ChartWidget
from host.gui.widgets.glass_card import GlassCard
from host.gui.widgets.stat_card import StatCard
from host.viewmodels.history_vm import HistoryViewModel
from common.i18n import tr

log = logging.getLogger("host.gui.history_page")

METRIC_COLORS = {
    "cpu.usage": TC.CHART_PRIMARY,
    "ram.usage": TC.CHART_GREEN,
    "gpu.usage": TC.CHART_ORANGE,
    "net.upload": TC.CHART_RED,
    "net.download": TC.CHART_PURPLE,
    "fps.value": TC.CHART_CYAN,
}
METRIC_LABELS = {
    "cpu.usage": "CPU", "ram.usage": "RAM", "gpu.usage": "GPU",
    "net.upload": "Upload", "net.download": "Download", "fps.value": "FPS",
}

_TIME_RANGES = [("10m", "10 分钟"), ("1h", "1 小时"), ("6h", "6 小时"),
                ("24h", "24 小时"), ("7d", "7 天")]


def _btn_style(active=False):
    bg = TC.ACCENT_PRIMARY if active else TC.BG_HOVER
    color = TC.TEXT_ON_COLOR if active else TC.TEXT_SECONDARY
    border = TC.ACCENT_PRIMARY if active else TC.BORDER_DEFAULT
    return f"""
        QPushButton {{ background: {bg}; color: {color};
            border: 1px solid {border}; border-radius: 8px;
            padding: 7px 14px; font-size: 12px; font-weight: 500; }}
        QPushButton:hover {{ border-color: {TC.ACCENT_PRIMARY}; }}
    """


class HistoryPage(PageBase):
    PAGE_ID = "history"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vm = None
        self._time_btns = {}
        self._metric_checks = {}
        self._current_range = "1h"
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(S.XL, S.LG, S.XL, S.LG)
        root.setSpacing(S.LG)

        # 控制卡：节点 + 时间范围 + 指标
        control = GlassCard()
        c_l = QHBoxLayout()
        c_l.setSpacing(S.MD)
        c_l.addWidget(self._lbl("节点"))
        self._node_combo = QComboBox()
        self._node_combo.setStyleSheet(
            f"QComboBox {{ background: {TC.BG_INPUT}; border: 1px solid {TC.BORDER_DEFAULT};"
            f" border-radius: 8px; padding: 6px 12px; font-size: 12px; color: {TC.TEXT_PRIMARY}; }}")
        self._node_combo.currentIndexChanged.connect(self._on_node_changed)
        c_l.addWidget(self._node_combo)
        c_l.addStretch(1)
        c_l.addWidget(self._lbl("时间"))
        for key, label in _TIME_RANGES:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(_btn_style(active=(key == "1h")))
            btn.clicked.connect(lambda checked, k=key: self._on_time(k))
            c_l.addWidget(btn)
            self._time_btns[key] = btn
        refresh = QPushButton("↻ 刷新")
        refresh.setStyleSheet(
            f"QPushButton {{ background: {TC.ACCENT_PRIMARY}; color: {TC.TEXT_ON_COLOR};"
            f" border: none; border-radius: 8px; padding: 7px 14px; font-size: 12px; font-weight: 600; }}")
        refresh.clicked.connect(self._on_refresh)
        self._refresh_btn = refresh
        c_l.addWidget(refresh)
        control._layout.addLayout(c_l)
        root.addWidget(control)

        # 指标勾选
        chk = QHBoxLayout()
        chk.setSpacing(S.MD)
        chk.addWidget(self._lbl("指标"))
        for key in ["cpu.usage", "ram.usage", "gpu.usage", "net.upload", "net.download"]:
            cb = QCheckBox(METRIC_LABELS.get(key, key))
            cb.setChecked(key in ("cpu.usage", "ram.usage", "gpu.usage"))
            cb.setStyleSheet(
                f"QCheckBox {{ color: {METRIC_COLORS.get(key, TC.TEXT_PRIMARY)};"
                f" font-size: 12px; font-weight: 600; spacing: 6px; }}")
            cb.toggled.connect(lambda checked, k=key: self._on_metric_toggle())
            chk.addWidget(cb)
            self._metric_checks[key] = cb
        chk.addStretch(1)
        root.addLayout(chk)

        # 图表面板
        panel = GlassCard()
        self._chart_title = QLabel("性能趋势")
        self._chart_title.setStyleSheet(
            f"font-size: {TT.TITLE_SMALL['size']}px; font-weight: 600;"
            f" color: {TC.TEXT_PRIMARY}; background: transparent;")
        panel._layout.addWidget(self._chart_title)
        self._chart = ChartWidget(title="", y_range=(0, 100))
        self._chart.setMinimumHeight(300)
        panel._layout.addWidget(self._chart, 1)
        root.addWidget(panel, 1)

        # 汇总卡
        summary = QHBoxLayout()
        summary.setSpacing(S.MD)
        self._card_avg = StatCard("平均", "—", TC.ACCENT_PRIMARY, sub="均值")
        self._card_peak = StatCard("峰值", "—", TC.STATUS_WARNING, sub="最大")
        self._card_count = StatCard("样本数", "—", TC.TEXT_PRIMARY, sub="数据点")
        for c in (self._card_avg, self._card_peak, self._card_count):
            summary.addWidget(c, 1)
        root.addLayout(summary)

        self._empty = QLabel("暂无数据，请选择节点与时间范围")
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: {TT.BODY['size']}px;"
            f" background: transparent;")
        self._empty.hide()
        root.addWidget(self._empty)

    def _lbl(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: {TT.BODY_SMALL['size']}px;"
            f" background: transparent;")
        return lbl

    def set_view_model(self, vm):
        self._vm = vm
        if vm:
            vm.data_changed.connect(self._refresh)
            vm.load_error.connect(lambda m: log.warning("history load error: %s", m))

    def on_show(self):
        super().on_show()
        self._refresh_node_combo()
        self._load_metrics()

    def _refresh_node_combo(self):
        if not self._vm:
            return
        self._node_combo.blockSignals(True)
        self._node_combo.clear()
        # 用 node_store 提供的节点（通过 set_stores）
        node_store = self.get_store("node")
        if node_store:
            for nid in node_store.node_ids():
                alias = node_store.get_alias(nid) or nid
                self._node_combo.addItem(alias, nid)
        self._node_combo.blockSignals(False)

    def _on_node_changed(self, idx):
        self._load_metrics()

    def _on_time(self, key):
        self._current_range = key
        for k, btn in self._time_btns.items():
            btn.setChecked(k == key)
            btn.setStyleSheet(_btn_style(active=(k == key)))
        self._load_metrics()

    def _on_refresh(self):
        self._load_metrics()

    def _on_metric_toggle(self):
        self._load_metrics()

    def _get_selected_metrics(self):
        return [k for k, cb in self._metric_checks.items() if cb.isChecked()]

    def _get_current_node(self):
        idx = self._node_combo.currentIndex()
        if idx < 0:
            return None
        return self._node_combo.itemData(idx)

    def _load_metrics(self):
        if not self._vm:
            return
        node_id = self._get_current_node()
        if not node_id:
            self._show_empty(True)
            return
        metrics = self._get_selected_metrics()
        if not metrics:
            self._show_empty(True)
            return
        start, end = self._vm.get_range_preset(self._current_range)
        self._vm.load_multi(node_id, metrics, start, end, limit=1000)
        self._refresh()

    def _show_empty(self, show):
        self._empty.setVisible(show)
        self._chart.setVisible(not show)

    def _refresh(self):
        if not self._vm:
            return
        multi = self._vm.get_multi_records()
        multi_summary = self._vm.get_multi_summary()
        if not any(multi.values()):
            self._show_empty(True)
            for c in (self._card_avg, self._card_peak, self._card_count):
                c.set_value("—")
            return
        self._show_empty(False)
        chart_series = {}
        for metric, records in multi.items():
            if records:
                chart_series[METRIC_LABELS.get(metric, metric)] = (
                    records, METRIC_COLORS.get(metric, TC.CHART_PRIMARY))
        self._chart.set_multi_series(chart_series)
        # 汇总
        all_avg, peak_val, total = [], None, 0
        for metric, summary in multi_summary.items():
            if summary.get("avg") is not None:
                all_avg.append(summary["avg"])
            if summary.get("max") is not None:
                peak_val = max(peak_val, summary["max"]) if peak_val is not None else summary["max"]
            total += summary.get("count", 0)
        avg_val = sum(all_avg) / len(all_avg) if all_avg else None
        self._card_avg.set_value(f"{avg_val:.1f}%" if avg_val is not None else "—")
        self._card_peak.set_value(f"{peak_val:.1f}%" if peak_val is not None else "—", color=TC.STATUS_WARNING)
        self._card_count.set_value(f"{total:,}")
