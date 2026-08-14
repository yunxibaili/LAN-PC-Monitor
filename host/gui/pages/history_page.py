# -*- coding: utf-8 -*-
"""
HistoryPage —— 历史趋势页（v5.2 Phase 5-4）。

Gentelella-inspired Desktop Console 风格。

数据流：
  HistoryPage → HistoryVM → HistoryFacade → MetricsRepository → SQLite

约束：
  - 不直接碰 Facade / Repository / sqlite3
  - 不自动刷新 / 不轮询
  - 复用 ChartWidget + SummaryCard
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.pages.base_page import PageBase
from host.gui.widgets.chart_widget import ChartWidget
from host.gui.widgets.chart_panel import SummaryCard
from host.viewmodels.history_vm import HistoryViewModel

log = logging.getLogger("host.gui.history_page")


class HistoryPage(PageBase):
    """历史趋势页：Header + Chart + Summary。"""

    PAGE_ID = "history"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vm = None
        self._current_range = "1h"
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(S.LG, S.SM, S.LG, S.SM)
        root.setSpacing(S.SM)

        # ---- Page Header ----
        header = QHBoxLayout()
        title = QLabel("History")
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {TC.TEXT_PRIMARY}; background: transparent;")
        header.addWidget(title)
        header.addStretch(1)
        root.addLayout(header)

        # ---- Controls ----
        controls = QFrame()
        controls.setStyleSheet(f"""
            QFrame {{
                background: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        ctrl_layout = QHBoxLayout(controls)
        ctrl_layout.setContentsMargins(S.MD, S.SM, S.MD, S.SM)
        ctrl_layout.setSpacing(S.MD)

        # Node
        node_col = QVBoxLayout()
        node_col.setSpacing(2)
        node_lbl = QLabel("Node")
        node_lbl.setStyleSheet(f"color: {TC.TEXT_DISABLED}; font-size: 11px; background: transparent;")
        node_col.addWidget(node_lbl)
        self._node_combo = QComboBox()
        self._node_combo.setFixedHeight(32)
        self._node_combo.setStyleSheet(f"""
            QComboBox {{
                background: {TC.BG_INPUT};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 8px;
                padding: 0 12px;
                color: {TC.TEXT_PRIMARY};
                font-size: 13px;
            }}
            QComboBox:focus {{ border-color: {TC.ACCENT_PRIMARY}; }}
        """)
        node_col.addWidget(self._node_combo)
        ctrl_layout.addLayout(node_col)

        # Metric
        metric_col = QVBoxLayout()
        metric_col.setSpacing(2)
        metric_lbl = QLabel("Metric")
        metric_lbl.setStyleSheet(f"color: {TC.TEXT_DISABLED}; font-size: 11px; background: transparent;")
        metric_col.addWidget(metric_lbl)
        self._metric_combo = QComboBox()
        self._metric_combo.setFixedHeight(32)
        for key, label in [("cpu.usage", "CPU Usage"), ("gpu.usage", "GPU Usage"),
                           ("ram.usage", "RAM Usage"), ("fps.value", "FPS"),
                           ("net.upload", "Upload"), ("net.download", "Download")]:
            self._metric_combo.addItem(label, key)
        self._metric_combo.setStyleSheet(self._node_combo.styleSheet())
        metric_col.addWidget(self._metric_combo)
        ctrl_layout.addLayout(metric_col)

        # Range
        range_col = QVBoxLayout()
        range_col.setSpacing(2)
        range_lbl = QLabel("Range")
        range_lbl.setStyleSheet(f"color: {TC.TEXT_DISABLED}; font-size: 11px; background: transparent;")
        range_col.addWidget(range_lbl)
        self._range_combo = QComboBox()
        self._range_combo.setFixedHeight(32)
        for key in ["5m", "30m", "1h", "6h", "24h"]:
            self._range_combo.addItem(f"Last {key}", key)
        self._range_combo.setCurrentIndex(2)  # default 1h
        self._range_combo.setStyleSheet(self._node_combo.styleSheet())
        range_col.addWidget(self._range_combo)
        ctrl_layout.addLayout(range_col)

        ctrl_layout.addStretch(1)

        # Load button
        self._load_btn = QPushButton("Load")
        self._load_btn.setFixedHeight(36)
        self._load_btn.setFixedWidth(80)
        self._load_btn.setStyleSheet(f"""
            QPushButton {{
                background: {TC.ACCENT_PRIMARY};
                color: {TC.TEXT_ON_COLOR};
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {TC.ACCENT_PRIMARY};
                border: 1px solid {TC.TEXT_PRIMARY};
            }}
        """)
        self._load_btn.clicked.connect(self._on_load)
        ctrl_layout.addWidget(self._load_btn)

        root.addWidget(controls)

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
        self._chart.setMinimumHeight(280)
        self._chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        chart_layout.addWidget(self._chart, 1)

        # Summary Cards
        summary_row = QHBoxLayout()
        summary_row.setSpacing(S.SM)
        self._card_avg = SummaryCard("AVG")
        self._card_max = SummaryCard("MAX")
        self._card_min = SummaryCard("MIN")
        self._card_count = SummaryCard("COUNT")
        summary_row.addWidget(self._card_avg)
        summary_row.addWidget(self._card_max)
        summary_row.addWidget(self._card_min)
        summary_row.addWidget(self._card_count)
        chart_layout.addLayout(summary_row)

        root.addWidget(chart_area, 1)

        # ---- Empty State ----
        self._empty = QLabel("No history data available\n\nStart monitoring to collect metrics")
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: 14px; background: transparent;")
        root.addWidget(self._empty)

    # ---------- ViewModel ----------

    def set_view_model(self, vm):
        self._vm = vm

    def update_node_list(self, nodes):
        """外部调用更新节点列表。"""
        self._node_combo.clear()
        self._node_combo.addItem("All Nodes", "")
        for node_id, alias in nodes:
            self._node_combo.addItem(alias or node_id, node_id)

    # ---------- 生命周期 ----------

    def on_show(self):
        super().on_show()

    def on_hide(self):
        super().on_hide()

    # ---------- 查询 ----------

    def _on_load(self):
        if not self._vm:
            return
        node_id = self._node_combo.currentData() or ""
        metric = self._metric_combo.currentData() or "cpu.usage"
        range_key = self._range_combo.currentData() or "1h"
        start, end = self._vm.get_range_preset(range_key)
        self._vm.load(node_id, metric, start, end)
        self._refresh()

    def _refresh(self):
        if not self._vm:
            return
        records = self._vm.get_records()
        summary = self._vm.get_summary()

        if not records:
            self._empty.show()
            self._chart.clear()
            self._card_avg.set_value("—")
            self._card_max.set_value("—")
            self._card_min.set_value("—")
            self._card_count.set_value("—")
            return

        self._empty.hide()

        # Chart
        metric = self._metric_combo.currentData() or "cpu.usage"
        self._chart.set_series(records)

        # Summary
        avg = summary.get("avg")
        mx = summary.get("max")
        mn = summary.get("min")
        count = summary.get("count", 0)
        self._card_avg.set_value(f"{avg:.1f}" if avg is not None else "—")
        self._card_max.set_value(f"{mx:.1f}" if mx is not None else "—")
        self._card_min.set_value(f"{mn:.1f}" if mn is not None else "—")
        self._card_count.set_value(str(count))
