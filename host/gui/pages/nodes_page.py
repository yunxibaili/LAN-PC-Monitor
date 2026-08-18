# -*- coding: utf-8 -*-
"""
DevicesPage —— 设备列表页（v5.3.4 Devices）。

Stats Row + Device Card Grid。
Signal 驱动，不直接访问 Store。
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea,
    QVBoxLayout, QWidget,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.pages.base_page import PageBase
from host.gui.widgets.device_card import DeviceCard
from common.i18n import tr

log = logging.getLogger("host.gui.devices_page")


class DevicesPage(PageBase):
    """设备列表页：Stats Row + Device Card Grid。"""

    PAGE_ID = "nodes"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vm = None
        self._cards = {}
        self._grid_cols = 3
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(S.LG, S.SM, S.LG, S.SM)
        root.setSpacing(S.SM)

        # Header
        header = QHBoxLayout()
        title = QLabel(tr("devices.title"))
        title.setStyleSheet(
            f"font-size: TT.TITLE_MEDIUM['size']px; font-weight:bold; color:{TC.TEXT_PRIMARY};"
            f" background:transparent;")
        header.addWidget(title)
        header.addStretch(1)
        self._subtitle = QLabel(tr("devices.subtitle"))
        self._subtitle.setStyleSheet(
            f"color:{TC.TEXT_SECONDARY}; font-size:TT.BODY['size']px; background:transparent;")
        header.addWidget(self._subtitle)
        root.addLayout(header)

        # Stats row
        stats = QHBoxLayout()
        stats.setSpacing(24)
        self._stat_online = self._make_stat("Online", "0", TC.STATUS_ONLINE)
        self._stat_offline = self._make_stat("Offline", "0", TC.STATUS_ERROR)
        self._stat_warning = self._make_stat("Warning", "0", TC.STATUS_WARNING)
        self._stat_total = self._make_stat("Total", "0", TC.TEXT_PRIMARY)
        root.addLayout(stats)
        root.addSpacing(8)

        # Device grid
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet("background:transparent; border:none;")
        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(S.SM)
        self._scroll.setWidget(self._grid_container)
        root.addWidget(self._scroll, 1)

        # Empty state
        self._empty = QLabel(tr("devices.no_device"))
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setStyleSheet(
            f"color:{TC.TEXT_DISABLED}; font-size:TT.BODY['size']px; background:transparent;"
            f" padding:40px 0;")
        self._empty.hide()
        root.addWidget(self._empty)

    def _make_stat(self, label, value, color):
        wrap = QVBoxLayout()
        wrap.setSpacing(0)
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(
            f"font-size:TT.NUMERIC_LARGE['size']px; font-weight:700; color:{color}; background:transparent;")
        name_lbl = QLabel(label)
        name_lbl.setStyleSheet(
            f"font-size:TT.BODY_SMALL['size']px; color:{TC.TEXT_SECONDARY}; background:transparent;")
        wrap.addWidget(val_lbl)
        wrap.addWidget(name_lbl)
        return {"val": val_lbl, "name": name_lbl}

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

        devices = self._vm.get_devices()
        summary = self._vm.get_summary()

        self._stat_online["val"].setText(str(summary["online"]))
        self._stat_offline["val"].setText(str(summary["offline"]))
        self._stat_warning["val"].setText(str(summary["warning"]))
        self._stat_total["val"].setText(str(summary["total"]))

        if not devices:
            self._empty.show()
            self._scroll.hide()
            return
        self._empty.hide()
        self._scroll.show()

        cols = self._calc_cols(self._scroll.viewport().width())
        for idx, dev in enumerate(devices):
            card = DeviceCard()
            card.update_device(dev)
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
                self._rebuild_grid()


# 向后兼容别名（tests 引用 NodesPage）
NodesPage = DevicesPage
