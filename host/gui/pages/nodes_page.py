# -*- coding: utf-8 -*-
"""
NodesPage —— 设备页（v5.5 白色高密度重设计）。

Stats Row(4 StatCard) + 设备卡片网格(NodeTile 响应式 1/2/3 列)。
Signal 驱动（devices_vm.data_changed），不 PULL 重建。
页面只调 VM API，不访问 Store。
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.pages.base_page import PageBase
from host.gui.widgets.glass_card import GlassCard
from host.gui.widgets.node_tile import NodeTile
from host.gui.widgets.stat_card import StatCard

log = logging.getLogger("host.gui.nodes_page")


class NodesPage(PageBase):
    PAGE_ID = "nodes"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vm = None
        self._cards = {}
        self._grid_cols = 3
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(S.XL, S.LG, S.XL, S.LG)
        root.setSpacing(S.LG)

        # 统计行
        stats = QHBoxLayout()
        stats.setSpacing(S.MD)
        self._stat_online = StatCard("在线", "0", TC.STATUS_ONLINE, sub="在线设备")
        self._stat_offline = StatCard("离线", "0", TC.DANGER, sub="离线设备")
        self._stat_warning = StatCard("警告", "0", TC.WARNING, sub="高负载")
        self._stat_total = StatCard("总数", "0", TC.ACCENT_PRIMARY, sub="登记设备")
        for c in (self._stat_online, self._stat_offline,
                  self._stat_warning, self._stat_total):
            stats.addWidget(c, 1)
        root.addLayout(stats)

        # 设备网格容器
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.NoFrame)
        self._scroll.setStyleSheet("background: transparent; border: none;")
        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background: transparent;")
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(S.MD)
        self._scroll.setWidget(self._grid_container)
        root.addWidget(self._scroll, 1)

        # 空状态
        self._empty = QLabel("暂无设备")
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: {TT.BODY['size']}px;"
            f" background: transparent; padding: 40px 0;")
        self._empty.hide()
        root.addWidget(self._empty)

    # ---- VM ----
    def set_view_model(self, vm):
        self._vm = vm
        if vm:
            vm.data_changed.connect(self._refresh)

    def on_show(self):
        super().on_show()
        self._refresh()

    def _refresh(self):
        if not self._vm:
            return
        devices = self._vm.get_devices()
        summary = self._vm.get_summary()
        self._stat_online.set_value(summary["online"], color=TC.STATUS_ONLINE)
        self._stat_offline.set_value(summary["offline"], color=TC.DANGER)
        self._stat_warning.set_value(summary["warning"], color=TC.WARNING)
        self._stat_total.set_value(summary["total"])

        # 重建网格
        for card in self._cards.values():
            self._grid_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

        if not devices:
            self._empty.show()
            self._scroll.hide()
            return
        self._empty.hide()
        self._scroll.show()

        cols = self._calc_cols(self._scroll.viewport().width())
        for idx, dev in enumerate(devices):
            card = NodeTile(dev.node_id, alias=dev.alias)
            card.update_data(dev)
            row, col = divmod(idx, cols)
            self._grid_layout.addWidget(card, row, col)
            self._cards[dev.node_id] = card

    def _calc_cols(self, width):
        if width < 900:
            return 1
        elif width < 1400:
            return 2
        return 3

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._cards:
            new_cols = self._calc_cols(self._scroll.viewport().width())
            if new_cols != self._grid_cols:
                self._grid_cols = new_cols
                self._refresh()


# 向后兼容别名（旧代码引用 NodesPage）
DevicesPage = NodesPage
