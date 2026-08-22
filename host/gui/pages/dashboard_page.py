# -*- coding: utf-8 -*-
"""
DashboardPage —— 总览页（v5.5 白色高密度重设计）。

布局：系统概览(4 MetricTile) → 双栏(实时指标 LiveChart + 最近告警 AlertEntry)
     → 已接入副机(NodeTile 横滚) → 底部 Summary(3 StatCard)
Signal 驱动，不访问 Store。
"""
import logging
import time
from collections import deque

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.pages.base_page import PageBase
from host.gui.widgets.chart_widget import ChartWidget
from host.gui.widgets.glass_card import GlassCard
from host.gui.widgets.metric_tile import MetricTile
from host.gui.widgets.node_tile import NodeTile
from host.gui.widgets.alert_entry import AlertEntry
from host.gui.widgets.stat_card import StatCard
from common.i18n import tr

log = logging.getLogger("host.gui.dashboard_page")

# 实时折线图颜色
_CHART_COLORS = {
    "CPU": TC.CHART_PRIMARY,
    "GPU": TC.CHART_ORANGE,
    "RAM": TC.CHART_GREEN,
    "NET": TC.CHART_CYAN,
}

# 最大保留点数（约 30 秒窗口，1 点/秒）
MAX_POINTS = 30


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
        self._agent_cards = {}  # node_id -> NodeTile

        # 100ms debounce（Signal 驱动，非轮询）
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(100)
        self._refresh_timer.timeout.connect(self._flush_refresh)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(S.XL, S.LG, S.XL, S.LG)
        root.setSpacing(S.LG)

        # ---- 系统概览: 4 MetricTile ----
        root.addWidget(self._section_label(tr("dashboard.system_overview")))
        tiles = QHBoxLayout()
        tiles.setSpacing(S.MD)
        self._tile_cpu = MetricTile("CPU", "%", TC.CHART_PRIMARY)
        self._tile_gpu = MetricTile("GPU", "%", TC.CHART_ORANGE)
        self._tile_ram = MetricTile("RAM", "%", TC.CHART_GREEN)
        self._tile_net = MetricTile("Network", "MB/s", TC.CHART_CYAN)
        for t in (self._tile_cpu, self._tile_gpu, self._tile_ram, self._tile_net):
            tiles.addWidget(t, 1)
        root.addLayout(tiles)

        # ---- 双栏: 实时指标 + 最近告警 ----
        two_col = QHBoxLayout()
        two_col.setSpacing(S.MD)

        # Left: 实时指标
        chart_card = GlassCard()
        chart_card._layout.setContentsMargins(S.MD, S.MD, S.MD, S.MD)
        chart_card._layout.setSpacing(S.SM)
        chart_header = QHBoxLayout()
        chart_title = QLabel("实时指标")
        chart_title.setStyleSheet(
            f"font-size: {TT.TITLE_SMALL['size']}px; font-weight: 600;"
            f" color: {TC.TEXT_PRIMARY}; background: transparent;")
        chart_header.addWidget(chart_title)
        chart_header.addWidget(QLabel("最近 30 秒"))
        chart_header.addStretch(1)
        chart_card._layout.addLayout(chart_header)

        self._chart = ChartWidget(title="", y_range=(0, 100))
        self._chart.set_window_seconds(MAX_POINTS)
        self._chart.set_show_x_values(False)
        self._chart.setMinimumHeight(260)
        chart_card._layout.addWidget(self._chart, 1)

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
        chart_card._layout.addLayout(legend)
        two_col.addWidget(chart_card, 2)

        # Right: 最近告警
        alerts_card = GlassCard()
        alerts_card._layout.setContentsMargins(S.MD, S.MD, S.MD, S.MD)
        alerts_card._layout.setSpacing(S.SM)
        alerts_header = QHBoxLayout()
        alerts_title = QLabel(tr("dashboard.recent_alerts"))
        alerts_title.setStyleSheet(
            f"font-size: {TT.TITLE_SMALL['size']}px; font-weight: 600;"
            f" color: {TC.TEXT_PRIMARY}; background: transparent;")
        alerts_header.addWidget(alerts_title)
        alerts_header.addStretch(1)
        alerts_card._layout.addLayout(alerts_header)

        self._alerts_area = QVBoxLayout()
        self._alerts_area.setSpacing(S.SM)
        self._alerts_area.addStretch(1)
        alerts_card._layout.addLayout(self._alerts_area)
        two_col.addWidget(alerts_card, 1)

        root.addLayout(two_col, 1)

        # ---- 已接入副机 ----
        self._agents_label = self._section_label(tr("dashboard.agents_online"))
        root.addWidget(self._agents_label)
        self._agents_scroll = self._make_agents_scroll()
        root.addWidget(self._agents_scroll)

        # ---- 底部 Summary ----
        summary_row = QHBoxLayout()
        summary_row.setSpacing(S.MD)
        self._card_total = StatCard(tr("dashboard.total_nodes"), "0", TC.ACCENT_PRIMARY, sub="登记节点")
        self._card_online = StatCard(tr("dashboard.online"), "0", TC.STATUS_ONLINE, sub="在线")
        self._card_alerts = StatCard(tr("dashboard.alerts"), "0", TC.WARNING, sub="活动告警")
        summary_row.addWidget(self._card_total)
        summary_row.addWidget(self._card_online)
        summary_row.addWidget(self._card_alerts)
        root.addLayout(summary_row)

    def _section_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: {TT.TITLE_SMALL['size']}px; font-weight: 600;"
            f" color: {TC.TEXT_PRIMARY}; background: transparent;")
        return lbl

    def _make_agents_scroll(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setFixedHeight(225)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._agents_container = QWidget()
        self._agents_layout = QHBoxLayout(self._agents_container)
        self._agents_layout.setContentsMargins(0, 0, 0, 0)
        self._agents_layout.setSpacing(S.MD)
        self._agents_layout.addStretch(1)
        scroll.setWidget(self._agents_container)
        return scroll

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
        self._update_summary_vm()
        self._refresh_alerts()
        self._refresh_agents()

    def update_trends(self, node_id, frame):
        """单帧到达时更新指标图块与折线图（唯一数据入口，读 frame 真值）。"""
        if not frame:
            return
        cpu = frame.get("cpu", {}).get("total_usage", 0)
        gpu = frame.get("gpu", {}).get("usage_percent", 0)
        ram = frame.get("ram", {}).get("usage_percent", 0)
        net = frame.get("net", {})
        net_val = net.get("upload_mb_s", 0) + net.get("download_mb_s", 0)
        self._tile_cpu.set_metric("CPU", cpu)
        self._tile_gpu.set_metric("GPU", gpu)
        self._tile_ram.set_metric("RAM", ram)
        self._tile_net.set_metric("Network", net_val, unit="MB/s")
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

    def _refresh_agents(self):
        online = []
        if self._vm:
            online = [n for n in self._vm.get_nodes()
                      if n.status in ("connected", "online")]
        for nid in list(self._agent_cards.keys()):
            if nid not in {n.node_id for n in online}:
                card = self._agent_cards.pop(nid)
                self._agents_layout.removeWidget(card)
                card.deleteLater()
        for n in online:
            card = self._agent_cards.get(n.node_id)
            if card is None:
                card = NodeTile(n.node_id, alias=n.alias)
                card.clicked.connect(self.card_clicked)
                self._agents_layout.insertWidget(
                    self._agents_layout.count() - 1, card)
                self._agent_cards[n.node_id] = card
            card.update_data(n)
        visible = bool(online)
        self._agents_label.setVisible(visible)
        self._agents_scroll.setVisible(visible)

    def _refresh_alerts(self):
        if not hasattr(self, '_alert_store') or not self._alert_store:
            return
        while self._alerts_area.count():
            item = self._alerts_area.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        alerts = self._alert_store.alerts(limit=5)
        if not alerts:
            lbl = QLabel("暂无告警")
            lbl.setStyleSheet(
                f"color: {TC.TEXT_DISABLED}; font-size: {TT.BODY_SMALL['size']}px;"
                f" padding: 12px; background: transparent;")
            self._alerts_area.addWidget(lbl)
            self._alerts_area.addStretch(1)
            return
        for a in alerts:
            entry = AlertEntry()
            entry.set_alert(a)
            self._alerts_area.addWidget(entry)
        self._alerts_area.addStretch(1)
