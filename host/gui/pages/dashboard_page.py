# -*- coding: utf-8 -*-
"""
DashboardPage —— 总览页（v5.2 Phase 4-2B）。

布局：PageHeader → SummaryCards → NodeCard Grid → TrendPanel → Recent Alerts
Signal 驱动，不访问 Store。
"""
import logging
import time

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea,
    QVBoxLayout, QWidget,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.pages.base_page import PageBase
from host.gui.widgets.node_card import NodeCard

log = logging.getLogger("host.gui.dashboard_page")


# ---------- SummaryCard ----------

class SummaryCard(QFrame):
    """KPI 统计卡片。"""

    def __init__(self, title="", value="0", color=None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self.setStyleSheet(f"""
            SummaryCard {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(S.MD, 10, S.MD, 10)
        layout.setSpacing(2)
        self._lbl = QLabel(title)
        self._lbl.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: 11px; background: transparent;")
        layout.addWidget(self._lbl)
        self._val = QLabel(value)
        self._val.setStyleSheet(
            f"color: {color or TC.TEXT_PRIMARY}; font-size: 28px; font-weight: bold; background: transparent;")
        layout.addWidget(self._val)

    def set_value(self, value, color=None):
        self._val.setText(str(value))
        if color:
            self._val.setStyleSheet(
                f"color: {color}; font-size: 28px; font-weight: bold; background: transparent;")


# ---------- AlertPreview ----------

class AlertPreviewItem(QFrame):
    """单条告警预览。"""

    def __init__(self, level="warn", title="", time_str="", parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet(f"""
            AlertPreviewItem {{
                background: transparent;
                border-bottom: 1px solid {TC.BORDER_DEFAULT};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        lv = QLabel("●")
        lv.setFixedWidth(12)
        color = TC.ALERT_DANGER if level == "red" else TC.ALERT_WARN if level == "warn" else TC.TEXT_SECONDARY
        lv.setStyleSheet(f"color: {color}; font-size: 12px; background: transparent;")
        layout.addWidget(lv)

        self._title = QLabel(title)
        self._title.setStyleSheet(f"color: {TC.TEXT_PRIMARY}; font-size: 12px; background: transparent;")
        layout.addWidget(self._title, 1)

        badge = QLabel(level.upper())
        badge.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 600; background: transparent;")
        layout.addWidget(badge)

        self._time = QLabel(time_str)
        self._time.setStyleSheet(f"color: {TC.TEXT_DISABLED}; font-size: 10px; background: transparent;")
        layout.addWidget(self._time)


# ---------- TrendPanel ----------

class TrendPanel(QFrame):
    """System Trend：4 个迷你趋势卡。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self.setStyleSheet(f"""
            TrendPanel {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(S.MD, S.SM, S.MD, S.SM)
        layout.setSpacing(S.SM)
        self._trends = {}
        for key, title in [("cpu", "CPU"), ("gpu", "GPU"), ("ram", "RAM"), ("net", "Network")]:
            w = QWidget()
            vl = QVBoxLayout(w)
            vl.setContentsMargins(0, 0, 0, 0)
            vl.setSpacing(0)
            lbl = QLabel(title)
            lbl.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: 10px; background: transparent;")
            val = QLabel("—")
            val.setStyleSheet(f"color: {TC.TEXT_PRIMARY}; font-size: 20px; font-weight: bold; background: transparent;")
            vl.addWidget(lbl)
            vl.addWidget(val)
            layout.addWidget(w, 1)
            self._trends[key] = val

    def update(self, key, value):
        val = self._trends.get(key)
        if val:
            val.setText(f"{value:.1f}")
            color = TC.bar_color(value)
            val.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold; background: transparent;")


# ---------- DashboardPage ----------

class DashboardPage(PageBase):
    """总览页。"""

    PAGE_ID = "dashboard"
    card_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vm = None
        self._cards = {}
        self._grid_cols = 2
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(S.LG, S.MD, S.LG, S.MD)
        root.setSpacing(S.MD)

        # Page Header
        hdr = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {TC.TEXT_PRIMARY};")
        hdr.addWidget(title)
        hdr.addStretch(1)
        self._subtitle = QLabel("System overview and performance at a glance")
        self._subtitle.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: 13px;")
        hdr.addWidget(self._subtitle)
        root.addLayout(hdr)

        # Summary Cards
        summary_row = QHBoxLayout()
        summary_row.setSpacing(S.SM)
        self._card_total = SummaryCard("Total Nodes", "0")
        self._card_online = SummaryCard("Online", "0", TC.SUCCESS)
        self._card_cpu = SummaryCard("Avg CPU", "0%")
        self._card_gpu = SummaryCard("Avg GPU", "0%")
        self._card_alerts = SummaryCard("Alerts", "0", TC.WARNING)
        summary_row.addWidget(self._card_total)
        summary_row.addWidget(self._card_online)
        summary_row.addWidget(self._card_cpu)
        summary_row.addWidget(self._card_gpu)
        summary_row.addWidget(self._card_alerts)
        root.addLayout(summary_row)

        # Node Overview Label
        self._nodes_label = QLabel("Node Overview")
        self._nodes_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {TC.TEXT_PRIMARY}; margin-top: 4px;")
        root.addWidget(self._nodes_label)

        # NodeCard Grid
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet(f"background: transparent; border: none;")
        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(S.SM)
        self._scroll.setWidget(self._grid_container)
        root.addWidget(self._scroll, 1)

        self._empty = QLabel("No online nodes detected")
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setStyleSheet(f"color: {TC.TEXT_DISABLED}; font-size: 14px; padding: 40px 0;")
        self._empty.hide()
        root.addWidget(self._empty)

        # System Trend
        self._trend = TrendPanel()
        root.addWidget(self._trend)

        # Recent Alerts
        self._alerts_title = QLabel("Recent Alerts")
        self._alerts_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {TC.TEXT_PRIMARY}; margin-top: 4px;")
        root.addWidget(self._alerts_title)
        self._alerts_container = QWidget()
        self._alerts_layout = QVBoxLayout(self._alerts_container)
        self._alerts_layout.setContentsMargins(0, 0, 0, 0)
        self._alerts_layout.setSpacing(0)
        root.addWidget(self._alerts_container)

    def set_view_model(self, vm):
        self._vm = vm

    def on_show(self):
        super().on_show()
        self._rebuild_grid()

    def _rebuild_grid(self):
        if not self._vm:
            return
        for card in self._cards.values():
            self._grid_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

        nodes = self._vm.get_nodes()
        if not nodes:
            self._empty.show()
            self._scroll.hide()
            self._update_summary(0, 0, 0)
            return

        self._empty.hide()
        self._scroll.show()

        cols = self._calc_cols(self._scroll.viewport().width())
        for idx, data in enumerate(nodes):
            card = NodeCard(data.node_id, alias=data.alias)
            card.update_data(data)
            card.clicked.connect(self._on_card_clicked)
            row, col = divmod(idx, cols)
            self._grid_layout.addWidget(card, row, col)
            self._cards[data.node_id] = card

        self._update_summary_from_vm()

    def _calc_cols(self, width):
        if width < 1000: return 1
        elif width < 1600: return 2
        elif width < 2200: return 3
        return 4

    def _update_summary(self, total, online, offline, alerts=0):
        self._card_total.set_value(total)
        self._card_online.set_value(online, TC.SUCCESS)
        self._card_cpu.set_value("--%")
        self._card_gpu.set_value("--%")
        self._card_alerts.set_value(alerts, TC.WARNING)

    def _update_summary_from_vm(self):
        if not self._vm: return
        nodes = self._vm.get_nodes()
        total = len(nodes)
        online = sum(1 for n in nodes if n.status in ("connected", "online"))
        self._update_summary(total, online, total - online)

    def update_trends(self, node_id, frame):
        if not frame: return
        self._trend.update("cpu", frame.get("cpu", {}).get("total_usage", 0))
        self._trend.update("gpu", frame.get("gpu", {}).get("usage_percent", 0))
        self._trend.update("ram", frame.get("ram", {}).get("usage_percent", 0))
        net = frame.get("net", {})
        self._trend.update("net", net.get("upload_mb_s", 0) + net.get("download_mb_s", 0))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._cards:
            new_cols = self._calc_cols(self._scroll.viewport().width())
            if new_cols != self._grid_cols:
                self._grid_cols = new_cols
                self._rebuild_grid()

    def _on_card_clicked(self, node_id):
        self.card_clicked.emit(node_id)
