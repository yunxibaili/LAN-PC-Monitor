# -*- coding: utf-8 -*-
"""
DashboardPage —— 总览页（v5.4 Gentelella 风格，实时折线图版）。

布局：Header → System Overview(4 MetricBar) → 双栏(实时折线图+告警) → Summary
Signal 驱动，不访问 Store。
"""
import logging
import time
from collections import deque

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.pages.base_page import PageBase
from host.gui.widgets.chart_panel import SummaryCard
from host.gui.widgets.metric_bar import MetricBar
from host.gui.widgets.chart_widget import ChartWidget
from common.i18n import tr

log = logging.getLogger("host.gui.dashboard_page")

# 实时折线图颜色
_CHART_COLORS = {
    "CPU": TC.CHART_PRIMARY,
    "GPU": TC.CHART_PURPLE,
    "RAM": TC.CHART_GREEN,
    "NET": TC.CHART_ORANGE,
}

# 最大保留点数
MAX_POINTS = 60


class _Point:
    """折线图数据点（兼容 ChartWidget，无需 MetricRecord）。"""
    __slots__ = ("timestamp", "value")

    def __init__(self, ts, value):
        self.timestamp = ts
        self.value = value


class DashboardPage(PageBase):
    PAGE_ID = "dashboard"
    card_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vm = None
        self._frame_store = None
        self._setup_ui()

        # 实时数据缓冲
        self._series = {k: deque(maxlen=MAX_POINTS) for k in ("CPU", "GPU", "RAM", "NET")}

        # 100ms debounce（Signal 驱动，非轮询）
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(100)
        self._refresh_timer.timeout.connect(self._flush_refresh)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(S.LG, S.MD, S.LG, S.MD)
        root.setSpacing(S.MD)

        # ---- Page Header ----
        header = QHBoxLayout()
        title = QLabel(tr("dashboard.title"))
        title.setStyleSheet(
            f"font-size: {TT.TITLE_LARGE['size']}px; font-weight: bold; "
            f"color: {TC.TEXT_PRIMARY}; background: transparent;")
        header.addWidget(title)
        header.addStretch(1)
        self._subtitle = QLabel(tr("dashboard.subtitle"))
        self._subtitle.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: {TT.BODY_SMALL['size']}px;"
            f" background: transparent;")
        header.addWidget(self._subtitle)
        root.addLayout(header)

        # ---- System Overview: 4 实时指标条 ----
        overview_label = QLabel(tr("dashboard.system_overview"))
        overview_label.setStyleSheet(
            f"font-size: {TT.TITLE_SMALL['size']}px; font-weight: 600; "
            f"color: {TC.TEXT_PRIMARY}; margin-top: 4px; background: transparent;")
        root.addWidget(overview_label)

        overview_card = QFrame()
        overview_card.setStyleSheet(f"background-color: {TC.BG_CARD}; border-radius: 8px;")
        overview_layout = QHBoxLayout(overview_card)
        overview_layout.setContentsMargins(S.LG, S.SM, S.LG, S.SM)
        overview_layout.setSpacing(S.XL)

        self._bar_cpu = MetricBar("CPU", "%", parent=overview_card)
        self._bar_gpu = MetricBar("GPU", "%", parent=overview_card)
        self._bar_ram = MetricBar("RAM", "%", parent=overview_card)
        self._bar_net = MetricBar("Network", "MB/s", parent=overview_card)
        overview_layout.addWidget(self._bar_cpu, 1)
        overview_layout.addWidget(self._bar_gpu, 1)
        overview_layout.addWidget(self._bar_ram, 1)
        overview_layout.addWidget(self._bar_net, 1)
        root.addWidget(overview_card)

        # ---- 双栏：实时折线图 + 最近告警 ----
        two_col = QHBoxLayout()
        two_col.setSpacing(S.SM)

        # Left: 实时折线图
        chart_card = QFrame()
        chart_card.setStyleSheet(f"background-color: {TC.BG_CARD}; border-radius: 8px;")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(S.SM, S.SM, S.SM, S.SM)
        chart_header = QHBoxLayout()
        chart_title = QLabel("实时指标")
        chart_title.setStyleSheet(
            f"font-size: {TT.TITLE_SMALL['size']}px; font-weight: 600;"
            f" color: {TC.TEXT_PRIMARY}; background: transparent;"
            f" padding: 4px 4px 8px 4px; border-bottom: 1px solid {TC.BORDER_DEFAULT};")
        chart_header.addWidget(chart_title)
        chart_header.addStretch(1)
        chart_layout.addLayout(chart_header)

        self._chart = ChartWidget(title="", y_range=(0, 100))
        self._chart.setMinimumHeight(240)
        chart_layout.addWidget(self._chart, 1)

        # 图例
        legend = QHBoxLayout()
        legend.setSpacing(S.LG)
        for name, color in _CHART_COLORS.items():
            item = QHBoxLayout()
            dot = QLabel("■")
            dot.setStyleSheet(f"color: {color}; font-size: 10px; background: transparent;")
            item.addWidget(dot)
            lbl = QLabel(name)
            lbl.setStyleSheet(
                f"color: {TC.TEXT_SECONDARY}; font-size: {TT.CAPTION['size']}px;"
                f" background: transparent;")
            item.addWidget(lbl)
            wrap = QWidget()
            wrap.setLayout(item)
            legend.addWidget(wrap)
        legend.addStretch(1)
        chart_layout.addLayout(legend)

        two_col.addWidget(chart_card, 2)

        # Right: 最近告警
        alerts_card = QFrame()
        alerts_card.setStyleSheet(f"background-color: {TC.BG_CARD}; border-radius: 8px;")
        alerts_layout = QVBoxLayout(alerts_card)
        alerts_layout.setContentsMargins(S.SM, S.SM, S.SM, S.SM)
        alerts_header = QHBoxLayout()
        alerts_title = QLabel(tr("dashboard.recent_alerts"))
        alerts_title.setStyleSheet(
            f"font-size: {TT.TITLE_SMALL['size']}px; font-weight: 600;"
            f" color: {TC.TEXT_PRIMARY}; background: transparent;"
            f" padding: 4px 4px 8px 4px; border-bottom: 1px solid {TC.BORDER_DEFAULT};")
        alerts_header.addWidget(alerts_title)
        alerts_header.addStretch(1)
        alerts_layout.addLayout(alerts_header)

        self._alerts_container = QVBoxLayout()
        self._alerts_container.setContentsMargins(0, 0, 0, 0)
        self._alerts_container.setSpacing(0)
        alerts_layout.addLayout(self._alerts_container)
        alerts_layout.addStretch(1)
        two_col.addWidget(alerts_card, 1)

        root.addLayout(two_col, 1)

        # ---- 底部 Summary ----
        summary_row = QHBoxLayout()
        summary_row.setSpacing(S.SM)
        self._card_total = SummaryCard(tr("dashboard.total_nodes"), "0",
                                        border_color=TC.ACCENT_PRIMARY, size=28)
        self._card_online = SummaryCard(tr("dashboard.online"), "0",
                                         TC.STATUS_ONLINE, border_color=TC.STATUS_ONLINE, size=28)
        self._card_alerts = SummaryCard(tr("dashboard.alerts"), "0",
                                         TC.WARNING, border_color=TC.WARNING, size=28)
        summary_row.addWidget(self._card_total)
        summary_row.addWidget(self._card_online)
        summary_row.addWidget(self._card_alerts)
        root.addLayout(summary_row)

    # ---------- 数据接入 ----------

    def set_view_model(self, vm):
        self._vm = vm

    def set_frame_store(self, frame_store):
        self._frame_store = frame_store
        if frame_store:
            frame_store.frame_updated.connect(self._on_frame_updated)

    def set_alert_store(self, alert_store):
        self._alert_store = alert_store

    def on_show(self):
        super().on_show()
        self._update_summary_vm()
        self._flush_refresh()

    def on_hide(self):
        super().on_hide()
        self._refresh_timer.stop()

    def _on_frame_updated(self, node_id, frame):
        if self._visible and not self._refresh_timer.isActive():
            self._refresh_timer.start()

    # ---------- 刷新 ----------

    def _update_summary_vm(self):
        if not self._vm:
            return
        nodes = self._vm.get_nodes()
        total = len(nodes)
        online = sum(1 for n in nodes if n.status in ("connected", "online"))
        alerts = 0
        if hasattr(self, '_alert_store') and self._alert_store:
            try:
                alerts = self._alert_store.active_count()
            except Exception:
                pass
        self._card_total.set_value(total)
        self._card_online.set_value(online, color=TC.STATUS_ONLINE)
        self._card_alerts.set_value(alerts, color=TC.WARNING)

    def _flush_refresh(self):
        if not self._vm:
            return
        nodes = self._vm.get_nodes()
        online = [n for n in nodes if n.status in ("connected", "online")]
        if not online:
            self._bar_cpu.set_metric("CPU", 0)
            self._bar_gpu.set_metric("GPU", 0)
            self._bar_ram.set_metric("RAM", 0)
            self._bar_net.set_metric("Network", 0, unit="MB/s")
            return

        avg = lambda fn: sum(fn(n) for n in online) / len(online)
        cpu = avg(lambda n: n.cpu_usage)
        gpu = avg(lambda n: n.gpu_usage)
        ram = avg(lambda n: n.memory_usage)
        net = avg(lambda n: n.network_rx + n.network_tx)

        # 更新实时指标条
        self._bar_cpu.set_metric("CPU", cpu)
        self._bar_gpu.set_metric("GPU", gpu)
        self._bar_ram.set_metric("RAM", ram)
        self._bar_net.set_metric("Network", net, unit="MB/s")

        # 追加到折线图缓冲
        now = time.time()
        self._series["CPU"].append(_Point(now, cpu))
        self._series["GPU"].append(_Point(now, gpu))
        self._series["RAM"].append(_Point(now, ram))
        self._series["NET"].append(_Point(now, net))

        # 刷新折线图
        chart_series = {}
        for name in ("CPU", "GPU", "RAM", "NET"):
            points = list(self._series[name])
            if points:
                chart_series[name] = (points, _CHART_COLORS[name])
        self._chart.set_multi_series(chart_series)

        self._update_summary_vm()
        self._refresh_alerts()

    def update_trends(self, node_id, frame):
        """外部信号：单帧到达时更新。"""
        if not frame:
            return
        cpu = frame.get("cpu", {}).get("total_usage", 0)
        gpu = frame.get("gpu", {}).get("usage_percent", 0)
        ram = frame.get("ram", {}).get("usage_percent", 0)
        net = frame.get("net", {})
        net_val = net.get("upload_mb_s", 0) + net.get("download_mb_s", 0)
        self._bar_cpu.set_metric("CPU", cpu)
        self._bar_gpu.set_metric("GPU", gpu)
        self._bar_ram.set_metric("RAM", ram)
        self._bar_net.set_metric("Network", net_val, unit="MB/s")
        now = time.time()
        self._series["CPU"].append(_Point(now, cpu))
        self._series["GPU"].append(_Point(now, gpu))
        self._series["RAM"].append(_Point(now, ram))
        self._series["NET"].append(_Point(now, net_val))
        chart_series = {}
        for name in ("CPU", "GPU", "RAM", "NET"):
            points = list(self._series[name])
            if points:
                chart_series[name] = (points, _CHART_COLORS[name])
        self._chart.set_multi_series(chart_series)

    def _refresh_alerts(self):
        if not hasattr(self, '_alert_store') or not self._alert_store:
            return
        while self._alerts_container.count():
            item = self._alerts_container.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        alerts = self._alert_store.alerts(limit=5)
        if not alerts:
            lbl = QLabel(tr("dashboard.no_alerts"))
            lbl.setStyleSheet(
                f"color: {TC.TEXT_DISABLED}; font-size: {TT.BODY_SMALL['size']}px;"
                f" padding: 12px; background: transparent;")
            self._alerts_container.addWidget(lbl)
            return

        for a in alerts:
            row = QFrame()
            row.setStyleSheet(
                f"background: transparent; border-bottom: 1px solid {TC.BORDER_DEFAULT};")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 8, 4, 8)
            row_layout.setSpacing(8)
            dot = QLabel("●")
            dot.setFixedWidth(12)
            color = TC.ALERT_DANGER if a.get("level") == "red" else TC.ALERT_WARN
            dot.setStyleSheet(f"color: {color}; font-size: 10px; background: transparent;")
            row_layout.addWidget(dot)
            col = QVBoxLayout()
            col.setSpacing(1)
            name = a.get("name") or a.get("path", "")
            val = a.get("value")
            title_txt = name + (f"  {val:.1f}%" if val is not None else "")
            tl = QLabel(title_txt)
            tl.setStyleSheet(
                f"font-size: {TT.BODY_SMALL['size']}px; font-weight: 600;"
                f" color: {TC.TEXT_PRIMARY}; background: transparent;")
            col.addWidget(tl)
            ts = a.get("timestamp", 0)
            if ts:
                ago = time.time() - ts
                time_txt = f"{a.get('node_alias', a.get('node_id', ''))} · {_fmt_ago(ago)}"
            else:
                time_txt = a.get("node_alias", "")
            ml = QLabel(time_txt)
            ml.setStyleSheet(
                f"font-size: {TT.CAPTION['size']}px; color: {TC.TEXT_SECONDARY};"
                f" background: transparent;")
            col.addWidget(ml)
            row_layout.addLayout(col, 1)
            self._alerts_container.addWidget(row)


def _fmt_ago(seconds):
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    return f"{int(seconds // 86400)}d ago"
