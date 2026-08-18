# -*- coding: utf-8 -*-
"""
DashboardPage —— 总览页（v5.3.2 Dashboard 2.0）。

布局：Header → SystemOverview → NodeCard Grid → Recent Alerts
Signal 驱动，不访问 Store。
"""
import logging

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea,
    QVBoxLayout, QWidget,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.theme.typography import ThemeTypography as TT
from common.i18n import tr
from host.gui.pages.base_page import PageBase
from host.gui.widgets.node_card import NodeCard
from host.gui.widgets.chart_panel import SummaryCard
from host.gui.widgets.metric_bar import MetricBar

log = logging.getLogger("host.gui.dashboard_page")


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


# ---------- SystemOverviewWidget ----------

class SystemOverviewWidget(QFrame):
    """System Overview：CPU / GPU / RAM / Network 全在同一行，带进度条。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            SystemOverviewWidget {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(S.MD, 10, S.MD, 10)
        layout.setSpacing(16)

        self._cpu = MetricBar("CPU", "%", parent=self)
        self._gpu = MetricBar("GPU", "%", parent=self)
        self._ram = MetricBar("RAM", "%", parent=self)
        self._net = MetricBar("Network", "MB/s", parent=self)

        for bar in (self._cpu, self._gpu, self._ram, self._net):
            layout.addWidget(bar, 1)

    def update_metrics(self, cpu: float = 0, gpu: float = 0, ram: float = 0,
                       net: float = 0):
        self._cpu.set_metric("CPU", cpu)
        self._gpu.set_metric("GPU", gpu)
        self._ram.set_metric("RAM", ram)
        self._net.set_metric("Network", net, unit="MB/s")


# ---------- DashboardPage ----------

class DashboardPage(PageBase):
    """总览页（v5.3.2 Dashboard 2.0）。"""

    PAGE_ID = "dashboard"
    card_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vm = None
        self._cards = {}
        self._grid_cols = 2
        self._setup_ui()

        # P1-6 fix: Signal 驱动 + 100ms debounce（非轮询）
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(100)
        self._refresh_timer.timeout.connect(self._flush_refresh)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(S.LG, S.MD, S.LG, S.MD)
        root.setSpacing(S.MD)

        # Page Header
        hdr = QHBoxLayout()
        title = QLabel(tr("dashboard.title"))
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {TC.TEXT_PRIMARY};")
        hdr.addWidget(title)
        hdr.addStretch(1)
        self._subtitle = QLabel(tr("dashboard.subtitle"))
        self._subtitle.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: {TT.BODY_SMALL['size']}px;")
        hdr.addWidget(self._subtitle)
        root.addLayout(hdr)

        # System Overview
        overview_label = QLabel(tr("dashboard.system_overview"))
        overview_label.setStyleSheet(
            f"font-size: {TT.TITLE_SMALL['size']}px; font-weight: 600; color: {TC.TEXT_PRIMARY};")
        root.addWidget(overview_label)
        self._system_overview = SystemOverviewWidget()
        root.addWidget(self._system_overview)

        # Node Overview
        self._nodes_label = QLabel(tr("dashboard.node_overview"))
        self._nodes_label.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {TC.TEXT_PRIMARY}; margin-top: 4px;")
        root.addWidget(self._nodes_label)

        # NodeCard Grid
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet("background: transparent; border: none;")
        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(S.SM)
        self._scroll.setWidget(self._grid_container)
        root.addWidget(self._scroll, 1)

        self._empty = QLabel(tr("devices.no_device"))
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: 14px; padding: 40px 0;")
        self._empty.hide()
        root.addWidget(self._empty)

        # Summary row
        summary_row = QHBoxLayout()
        summary_row.setSpacing(S.SM)
        self._card_total = SummaryCard(tr("dashboard.total_nodes"), "0", size=28, border_color=TC.ACCENT_PRIMARY)
        self._card_online = SummaryCard(tr("dashboard.online"), "0", TC.SUCCESS, size=28, border_color=TC.SUCCESS)
        self._card_alerts = SummaryCard(tr("dashboard.alerts"), "0", TC.WARNING, size=28, border_color=TC.WARNING)
        summary_row.addWidget(self._card_total)
        summary_row.addWidget(self._card_online)
        summary_row.addWidget(self._card_alerts)
        root.addLayout(summary_row)

        # Recent Alerts
        self._alerts_title = QLabel(tr("dashboard.recent_alerts"))
        self._alerts_title.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {TC.TEXT_PRIMARY}; margin-top: 4px;")
        root.addWidget(self._alerts_title)
        self._alerts_container = QWidget()
        self._alerts_layout = QVBoxLayout(self._alerts_container)
        self._alerts_layout.setContentsMargins(0, 0, 0, 0)
        self._alerts_layout.setSpacing(0)
        root.addWidget(self._alerts_container)

    def set_view_model(self, vm):
        self._vm = vm

    def set_frame_store(self, frame_store):
        """P1-6: 连接 frame_store 信号，触发 Signal 驱动刷新。"""
        self._frame_store = frame_store
        if frame_store:
            frame_store.frame_updated.connect(self._on_frame_updated)

    def _on_frame_updated(self, node_id, frame):
        """P1-6: 帧到达 → 启动 debounce timer（非轮询）。"""
        if self._visible and not self._refresh_timer.isActive():
            self._refresh_timer.start()

    def set_alert_store(self, alert_store):
        self._alert_store = alert_store

    def set_alert_store(self, alert_store):
        """接收 AlertStore（可选，v5.3.2 增强告警预览）。"""
        self._alert_store = alert_store

    def on_show(self):
        super().on_show()
        self._rebuild_grid()
        self._flush_refresh()

    def on_hide(self):
        super().on_hide()
        self._refresh_timer.stop()

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
            self._system_overview.update_metrics(0, 0, 0, 0)
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
        self._flush_refresh()

    def _calc_cols(self, width):
        if width < 1000:
            return 1
        elif width < 1600:
            return 2
        elif width < 2200:
            return 3
        return 4

    def _update_summary(self, total, online, offline, alerts=0):
        self._card_total.set_value(total)
        self._card_online.set_value(online, color=TC.SUCCESS)
        self._card_alerts.set_value(alerts, color=TC.WARNING)

    def _update_summary_from_vm(self):
        if not self._vm:
            return
        nodes = self._vm.get_nodes()
        total = len(nodes)
        online = sum(1 for n in nodes if n.status in ("connected", "online"))
        alerts = 0
        if hasattr(self, '_alert_store') and self._alert_store:
            try:
                alerts = self._alert_store.count()
            except Exception:
                pass
        self._update_summary(total, online, total - online, alerts)

    def _flush_refresh(self):
        """2 秒节流刷新 System Overview + Summary Cards + Alerts。"""
        if not self._vm:
            return
        nodes = self._vm.get_nodes()
        if not nodes:
            return
        online = [n for n in nodes if n.status in ("connected", "online")]
        if not online:
            return
        # 聚合：取所有在线节点均值
        avg = lambda fn: sum(fn(n) for n in online) / len(online)
        self._system_overview.update_metrics(
            cpu=avg(lambda n: n.cpu_usage),
            gpu=avg(lambda n: n.gpu_usage),
            ram=avg(lambda n: n.memory_usage),
            net=avg(lambda n: n.network_rx + n.network_tx),
        )
        self._refresh_alerts()

    def _refresh_alerts(self):
        """刷新 Recent Activity（从 AlertStore 取最近 5 条）。"""
        if not hasattr(self, '_alert_store') or not self._alert_store:
            return
        # 清空旧内容
        while self._alerts_layout.count():
            item = self._alerts_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        alerts = self._alert_store.alerts(limit=5)
        if not alerts:
            lbl = QLabel(tr("dashboard.no_alerts"))
            lbl.setStyleSheet(
                f"color:{TC.TEXT_DISABLED}; font-size:12px; padding:12px;"
                f" background:transparent;")
            self._alerts_layout.addWidget(lbl)
            return

        for a in alerts:
            row = QHBoxLayout()
            row.setContentsMargins(0, 8, 0, 8)
            row.setSpacing(10)

            dot = QLabel("●")
            dot.setFixedWidth(12)
            color = TC.ALERT_DANGER if a.get("level") == "red" else TC.ALERT_WARN
            dot.setStyleSheet(f"color:{color}; font-size:10px; background:transparent;")
            row.addWidget(dot)

            col = QVBoxLayout()
            col.setSpacing(1)
            name = a.get("name") or a.get("path", "")
            val = a.get("value")
            node = a.get("node_alias") or a.get("node_id", "")
            title_txt = name
            if val is not None:
                title_txt += f"  {val:.1f}%"
            title_lbl = QLabel(title_txt)
            title_lbl.setStyleSheet(
                f"font-size:12px; font-weight:600; color:{TC.TEXT_PRIMARY};"
                f" background:transparent;")
            col.addWidget(title_lbl)

            ts = a.get("timestamp", 0)
            if ts:
                import time as _t
                ago = _t.time() - ts
                if ago < 60:
                    time_txt = f"{node} · {int(ago)}s ago"
                elif ago < 3600:
                    time_txt = f"{node} · {int(ago // 60)}m ago"
                else:
                    time_txt = f"{node} · {int(ago // 3600)}h ago"
            else:
                time_txt = node
            meta_lbl = QLabel(time_txt)
            meta_lbl.setStyleSheet(
                f"font-size:11px; color:{TC.TEXT_SECONDARY}; background:transparent;")
            col.addWidget(meta_lbl)

            row.addLayout(col, 1)
            self._alerts_layout.addLayout(row)

    def update_trends(self, node_id, frame):
        """外部调用（MainWindow 信号驱动）。"""
        if not frame:
            return
        self._system_overview.update_metrics(
            cpu=frame.get("cpu", {}).get("total_usage", 0),
            gpu=frame.get("gpu", {}).get("usage_percent", 0),
            ram=frame.get("ram", {}).get("usage_percent", 0),
            net=frame.get("net", {}).get("upload_mb_s", 0)
                 + frame.get("net", {}).get("download_mb_s", 0),
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._cards:
            new_cols = self._calc_cols(self._scroll.viewport().width())
            if new_cols != self._grid_cols:
                self._grid_cols = new_cols
                self._rebuild_grid()

    def _on_card_clicked(self, node_id):
        self.card_clicked.emit(node_id)
