# -*- coding: utf-8 -*-
"""
HistoryPage —— 历史趋势页（v5.3.3 History UX）。

布局：Header → TimeButtons → MetricCheckboxes → Chart → SummaryCards
Signal 驱动，不访问 Store / Facade / Repository。
"""
import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.pages.base_page import PageBase
from host.gui.widgets.chart_widget import ChartWidget
from host.gui.widgets.chart_panel import SummaryCard
from host.viewmodels.history_vm import HistoryViewModel
from common.i18n import tr

log = logging.getLogger("host.gui.history_page")

# 多曲线颜色
METRIC_COLORS = {
    "cpu.usage":     TC.CHART_PRIMARY,
    "ram.usage":     TC.CHART_SECONDARY,
    "gpu.usage":     TC.CHART_GREEN,
    "net.upload":    TC.CHART_RED,
    "net.download":  TC.CHART_PURPLE,
    "fps.value":     TC.CHART_CYAN,
}

METRIC_LABELS = {
    "cpu.usage": "CPU",
    "ram.usage": "RAM",
    "gpu.usage": "GPU",
    "net.upload": "Upload",
    "net.download": "Download",
    "fps.value": "FPS",
}


def _btn_style(active=False):
    bg = TC.ACCENT_PRIMARY if active else TC.BG_CARD
    border = TC.ACCENT_PRIMARY if active else TC.BORDER_DEFAULT
    color = TC.TEXT_ON_COLOR if active else TC.TEXT_PRIMARY
    return f"""
        QPushButton {{
            background: {bg};
            color: {color};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 6px 14px;
            font-size: 12px;
            font-weight: 600;
            min-width: 44px;
        }}
        QPushButton:hover {{
            border: 1px solid {TC.ACCENT_PRIMARY};
        }}
    """


def _check_style(color):
    return f"""
        QCheckBox {{
            color: {color};
            font-size: 12px;
            font-weight: 600;
            spacing: 6px;
            background: transparent;
        }}
        QCheckBox::indicator {{
            width: 14px; height: 14px;
            border: 2px solid {color};
            border-radius: 3px;
            background: transparent;
        }}
        QCheckBox::indicator:checked {{
            background: {color};
        }}
    """


class HistoryPage(PageBase):
    """历史趋势页（v5.3.3 History UX）。"""

    PAGE_ID = "history"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vm = None
        self._time_btns = {}
        self._metric_checks = {}
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(S.LG, S.SM, S.LG, S.SM)
        root.setSpacing(S.SM)

        # ---- Header ----
        header = QHBoxLayout()
        title = QLabel(tr("history.title"))
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {TC.TEXT_PRIMARY};"
            f" background: transparent;")
        header.addWidget(title)
        header.addStretch(1)
        root.addLayout(header)

        # ---- Time Range Buttons ----
        time_row = QHBoxLayout()
        time_row.setSpacing(S.SM)
        time_lbl = QLabel(tr("history.time_range"))
        time_lbl.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        time_row.addWidget(time_lbl)

        self._time_btns = {}
        for key, label in [("10m", "10 min"), ("1h", "1 hour"),
                           ("6h", "6 hours"), ("24h", "24 hours"),
                           ("7d", "7 days")]:
            btn = QPushButton(label)
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda checked, k=key: self._on_time_click(k))
            self._time_btns[key] = btn
            time_row.addWidget(btn)

        time_row.addStretch(1)

        self._refresh_btn = QPushButton("↻ Refresh")
        self._refresh_btn.setFixedHeight(30)
        self._refresh_btn.setStyleSheet(_btn_style())
        self._refresh_btn.clicked.connect(self._on_refresh)
        time_row.addWidget(self._refresh_btn)

        root.addLayout(time_row)

        # ---- Metric Checkboxes ----
        metric_row = QHBoxLayout()
        metric_row.setSpacing(S.SM)
        metric_lbl = QLabel(tr("history.metrics"))
        metric_lbl.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        metric_row.addWidget(metric_lbl)

        self._metric_checks = {}
        for key in ["cpu.usage", "ram.usage", "gpu.usage", "net.upload", "net.download"]:
            cb = QCheckBox(METRIC_LABELS.get(key, key))
            cb.setStyleSheet(_check_style(METRIC_COLORS.get(key, TC.TEXT_PRIMARY)))
            cb.toggled.connect(lambda checked, k=key: self._on_metric_toggle(k, checked))
            self._metric_checks[key] = cb
            metric_row.addWidget(cb)

        # 默认选中 CPU
        self._metric_checks["cpu.usage"].setChecked(True)

        metric_row.addStretch(1)
        root.addLayout(metric_row)

        # ---- Chart + Summary ----
        chart_area = QFrame()
        chart_area.setStyleSheet(f"""
            QFrame {{
                background: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        chart_layout = QVBoxLayout(chart_area)
        chart_layout.setContentsMargins(S.SM, S.SM, S.SM, S.SM)
        chart_layout.setSpacing(S.SM)

        self._chart = ChartWidget(title="", y_range=(0, 100))
        self._chart.setMinimumHeight(300)
        self._chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        chart_layout.addWidget(self._chart, 1)

        # Summary Cards
        summary_row = QHBoxLayout()
        summary_row.setSpacing(S.SM)
        self._card_avg = SummaryCard("Average", "—", TC.CHART_PRIMARY, size=22)
        self._card_peak = SummaryCard("Peak", "—", TC.BAR_DANGER, size=22)
        self._card_count = SummaryCard("Samples", "—", size=22)
        summary_row.addWidget(self._card_avg)
        summary_row.addWidget(self._card_peak)
        summary_row.addWidget(self._card_count)
        chart_layout.addLayout(summary_row)

        root.addWidget(chart_area, 1)

        # ---- Empty State ----
        self._empty = QLabel(tr("history.no_data"))
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: 14px; background: transparent;")
        root.addWidget(self._empty)

    # ---- ViewModel ----

    def set_view_model(self, vm):
        self._vm = vm

    def update_node_list(self, nodes):
        """外部调用更新节点列表（保留接口兼容）。"""
        pass

    # ---- Time Button ----

    def _on_time_click(self, key):
        # 视觉反馈
        for k, btn in self._time_btns.items():
            btn.setStyleSheet(_btn_style(active=(k == key)))
        # 自动加载
        self._load_metrics(key)

    def _on_refresh(self):
        # 找当前激活的 time range
        active = "1h"
        for k, btn in self._time_btns.items():
            if "border: 1px solid " + TC.ACCENT_PRIMARY in btn.styleSheet():
                active = k
                break
        self._load_metrics(active)

    def _on_metric_toggle(self, key, checked):
        pass  # 需要用户点击 Refresh 才刷新

    # ---- 数据加载 ----

    def _get_selected_metrics(self):
        return [k for k, cb in self._metric_checks.items() if cb.isChecked()]

    def _load_metrics(self, range_key="1h"):
        if not self._vm:
            return
        metrics = self._get_selected_metrics()
        if not metrics:
            self._show_empty(True)
            return

        # 需要 node_id — 从 VM 内部状态获取（如果有）
        # 这里使用 "all" 或空串表示查询所有节点聚合
        # 实际使用时 MainWindow 会设置当前 node_id
        node_id = getattr(self._vm, '_current_node', '') or ""
        if not node_id:
            self._show_empty(True)
            return

        start, end = self._vm.get_range_preset(range_key)
        self._vm.load_multi(node_id, metrics, start, end)
        self._refresh()

    def _show_empty(self, show):
        self._empty.setVisible(show)
        self._chart.setVisible(not show)

    # ---- 刷新显示 ----

    def _refresh(self):
        if not self._vm:
            return

        multi_records = self._vm.get_multi_records()
        multi_summary = self._vm.get_multi_summary()

        if not any(multi_records.values()):
            self._show_empty(True)
            self._card_avg.set_value("—")
            self._card_peak.set_value("—")
            self._card_count.set_value("—")
            return

        self._show_empty(False)

        # Chart: 多曲线叠加
        chart_series = {}
        for metric, records in multi_records.items():
            if records:
                color = METRIC_COLORS.get(metric, TC.CHART_PRIMARY)
                label = METRIC_LABELS.get(metric, metric)
                chart_series[label] = (records, color)
        self._chart.set_multi_series(chart_series)

        # Summary: 聚合所有选中指标
        all_values = []
        peak_val = None
        total_count = 0
        for metric, summary in multi_summary.items():
            if summary["avg"] is not None:
                all_values.append(summary["avg"])
            if summary["max"] is not None:
                if peak_val is None or summary["max"] > peak_val:
                    peak_val = summary["max"]
            total_count += summary.get("count", 0)

        avg_val = sum(all_values) / len(all_values) if all_values else None
        self._card_avg.set_value(f"{avg_val:.1f}%" if avg_val is not None else "—")
        self._card_peak.set_value(f"{peak_val:.1f}%" if peak_val is not None else "—")
        self._card_count.set_value(f"{total_count:,}")

    # ---- 生命周期 ----

    def on_show(self):
        super().on_show()
        # 初始化 time button 样式
        for k, btn in self._time_btns.items():
            btn.setStyleSheet(_btn_style(active=(k == "1h")))

    def on_hide(self):
        super().on_hide()
