# -*- coding: utf-8 -*-
"""
AlertsPage —— 告警中心页（v5.2 Phase 4-5 / 4-5.1 修复）。

数据流：
  AlertViewModel.alerts_changed → _on_alerts_changed → _refresh
  AlertViewModel.count_changed  → _on_count_changed → 更新统计

约束：
  - 不直接访问 AlertStore / AlertEngine / FrameStore
  - 不 QTimer
  - 纯 Signal 驱动

布局：
  PageHeader → AlertSummaryRow → AlertToolbar → AlertTimeline → AlertDetail
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.pages.base_page import PageBase
from host.gui.widgets.alert_summary_card import AlertSummaryCard
from common.i18n import tr
from host.gui.widgets.alert_card import AlertCard
from host.gui.widgets.alert_toolbar import AlertToolbar
from host.gui.widgets.alert_detail import AlertDetail

log = logging.getLogger("host.gui.alerts_page")


class AlertsPage(PageBase):
    """告警中心页：统计 + 过滤 + 告警卡片列表 + 详情。"""

    PAGE_ID = "alerts"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vm = None
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(S.LG, S.SM, S.LG, S.SM)
        root.setSpacing(S.SM)

        # ---- Page Header ----
        header = QHBoxLayout()
        header.setSpacing(S.SM)
        title = QLabel(tr("alerts.title"))
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {TC.TEXT_PRIMARY}; background: transparent;")
        header.addWidget(title)
        header.addStretch(1)
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        header.addWidget(self._status_lbl)
        root.addLayout(header)

        # ---- Summary Row (4 cards: Critical / Warning / Active / Total) ----
        summary_row = QHBoxLayout()
        summary_row.setSpacing(S.SM)
        self._card_critical = AlertSummaryCard("CRITICAL", TC.STATUS_ERROR)
        self._card_warning = AlertSummaryCard("WARNING", TC.STATUS_WARNING)
        self._card_active = AlertSummaryCard("ACTIVE", TC.ACCENT_PRIMARY)
        self._card_total = AlertSummaryCard("TOTAL", TC.TEXT_PRIMARY)
        summary_row.addWidget(self._card_critical)
        summary_row.addWidget(self._card_warning)
        summary_row.addWidget(self._card_active)
        summary_row.addWidget(self._card_total)
        root.addLayout(summary_row)

        # ---- Toolbar ----
        self._toolbar = AlertToolbar()
        self._toolbar.filter_changed.connect(self._on_filter_changed)
        self._toolbar.clear_clicked.connect(self._on_clear_all)
        root.addWidget(self._toolbar)

        # ---- Alert List (scrollable) ----
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(S.SM)
        self._list_layout.addStretch(1)
        scroll.setWidget(self._list_container)
        root.addWidget(scroll, 1)

        # ---- Empty state ----
        self._empty_label = QLabel("暂无告警")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: 15px; padding: 40px 0; background: transparent;")
        root.addWidget(self._empty_label)

        # ---- Detail Panel ----
        self._detail = AlertDetail()
        root.addWidget(self._detail)

    # ---------- ViewModel 注入 ----------

    def set_view_model(self, vm) -> None:
        self._vm = vm
        vm.alerts_changed.connect(self._on_alerts_changed)
        vm.count_changed.connect(self._on_count_changed)

    # ---------- 生命周期 ----------

    def on_show(self) -> None:
        super().on_show()
        self._refresh()

    def on_hide(self) -> None:
        super().on_hide()

    def cleanup(self) -> None:
        if self._vm:
            try:
                self._vm.alerts_changed.disconnect(self._on_alerts_changed)
                self._vm.count_changed.disconnect(self._on_count_changed)
            except (TypeError, RuntimeError):
                pass

    # ---------- 信号回调 ----------

    def _on_alerts_changed(self) -> None:
        self._refresh()

    def _on_count_changed(self, count: int) -> None:
        self._refresh_summary()

    # ---------- 过滤 ----------

    def _on_filter_changed(self) -> None:
        if not self._vm:
            return
        self._vm.set_filter_level(self._toolbar.get_level_filter())
        self._vm.set_filter_node(self._toolbar.get_node_filter())
        self._vm.set_search(self._toolbar.get_search_text())
        self._refresh_list()

    def _on_clear_all(self) -> None:
        if self._vm:
            self._vm.clear_all()

    # ---------- 刷新 ----------

    def _refresh(self) -> None:
        self._refresh_summary()
        self._refresh_list()

    def _refresh_summary(self) -> None:
        if not self._vm:
            return
        self._card_critical.set_value(self._vm.get_red_count())
        self._card_warning.set_value(self._vm.get_warn_count())
        self._card_active.set_value(self._vm.get_count())
        summary = self._vm.get_summary()
        self._card_total.set_value(summary.get("total", 0))
        self._status_lbl.setText(f"{self._vm.get_count()} active alerts")

    def _refresh_list(self) -> None:
        if not self._vm:
            return

        # 清除旧卡片
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        items = self._vm.get_items()

        if not items:
            self._empty_label.show()
            self._detail.clear()
            return

        self._empty_label.hide()

        for alert_item in items:
            card = AlertCard()
            card.set_alert(alert_item)
            card.clicked.connect(self._on_card_clicked)
            self._list_layout.addWidget(card)

        self._list_layout.addStretch(1)

    def _on_card_clicked(self, alert_item) -> None:
        """卡片被点击 → 显示详情。"""
        if alert_item is None:
            return
        self._detail.set_alert(alert_item)

    # ---------- 向后兼容 ----------

    def update_node_list(self, nodes: list) -> None:
        self._toolbar.update_node_list(nodes)

    def _card_count(self) -> int:
        """返回当前显示的卡片数量。"""
        count = 0
        for i in range(self._list_layout.count()):
            w = self._list_layout.itemAt(i).widget()
            if isinstance(w, AlertCard):
                count += 1
        return count
