# -*- coding: utf-8 -*-
"""
AlertsPage —— 告警中心页（v5.5 白色高密度重设计）。

Stats(4 StatCard) → Toolbar(等级/节点过滤/搜索/清除) → 告警列表(AlertEntry) → 详情。
Signal 驱动（alert_vm.alerts_changed / count_changed）。
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QScrollArea, QVBoxLayout, QWidget,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.pages.base_page import PageBase
from host.gui.widgets.glass_card import GlassCard
from host.gui.widgets.alert_entry import AlertEntry
from host.gui.widgets.stat_card import StatCard
from host.gui.widgets.alert_detail import AlertDetail

log = logging.getLogger("host.gui.alerts_page")


def _chip_style(active=False):
    bg = TC.ACCENT_PRIMARY if active else TC.BG_HOVER
    color = TC.TEXT_ON_COLOR if active else TC.TEXT_SECONDARY
    border = TC.ACCENT_PRIMARY if active else TC.BORDER_DEFAULT
    return f"""
        QPushButton {{
            background: {bg}; color: {color};
            border: 1px solid {border}; border-radius: 8px;
            padding: 6px 14px; font-size: 12px; font-weight: 500;
        }}
        QPushButton:hover {{ border-color: {TC.ACCENT_PRIMARY}; }}
    """


class AlertsPage(PageBase):
    PAGE_ID = "alerts"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vm = None
        self._level_filters = {}
        self._current_level = None
        self._empty_label = None
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(S.XL, S.LG, S.XL, S.LG)
        root.setSpacing(S.LG)

        # 统计行
        stats = QHBoxLayout()
        stats.setSpacing(S.MD)
        self._card_critical = StatCard("严重", "0", TC.DANGER, sub="Critical")
        self._card_warning = StatCard("警告", "0", TC.WARNING, sub="Warning")
        self._card_active = StatCard("活动", "0", TC.ACCENT_PRIMARY, sub="当前")
        self._card_total = StatCard("总数", "0", TC.TEXT_PRIMARY, sub="全部")
        for c in (self._card_critical, self._card_warning,
                  self._card_active, self._card_total):
            stats.addWidget(c, 1)
        root.addLayout(stats)

        # 工具栏
        toolbar = GlassCard()
        bar_l = QHBoxLayout()
        bar_l.setSpacing(S.SM)
        self._level_btns = {}
        for level, label in [(None, "全部"), ("red", "严重"), ("warn", "警告")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(_chip_style(active=(level is None)))
            btn.clicked.connect(lambda checked, lv=level: self._set_level(lv))
            bar_l.addWidget(btn)
            self._level_btns[level] = btn

        self._node_combo = QComboBox()
        self._node_combo.setStyleSheet(
            f"QComboBox {{ background: {TC.BG_INPUT}; border: 1px solid {TC.BORDER_DEFAULT};"
            f" border-radius: 8px; padding: 6px 12px; font-size: 12px; color: {TC.TEXT_PRIMARY}; }}")
        self._node_combo.currentIndexChanged.connect(self._on_node_changed)
        bar_l.addWidget(self._node_combo)

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索告警关键词…")
        self._search.setStyleSheet(
            f"QLineEdit {{ background: {TC.BG_INPUT}; border: 1px solid {TC.BORDER_DEFAULT};"
            f" border-radius: 8px; padding: 6px 12px; font-size: 12px; color: {TC.TEXT_PRIMARY}; }}")
        self._search.textChanged.connect(self._on_search)
        bar_l.addWidget(self._search, 1)

        clear_btn = QPushButton("清除告警")
        clear_btn.setStyleSheet(
            f"QPushButton {{ background: rgba(214,57,57,0.10); color: {TC.DANGER};"
            f" border: 1px solid rgba(214,57,57,0.3); border-radius: 8px;"
            f" padding: 6px 14px; font-size: 12px; }}")
        clear_btn.clicked.connect(self._on_clear_all)
        bar_l.addWidget(clear_btn)
        toolbar._layout.addLayout(bar_l)
        root.addWidget(toolbar)

        # 列表 + 详情 双栏
        body = QHBoxLayout()
        body.setSpacing(S.MD)

        # 列表
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.NoFrame)
        self._scroll.setStyleSheet("background: transparent; border: none;")
        self._list_holder = QWidget()
        self._list_holder.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_holder)
        self._list_layout.setSpacing(S.SM)
        self._list_layout.addStretch(1)
        self._scroll.setWidget(self._list_holder)
        body.addWidget(self._scroll, 3)

        # 详情
        self._detail = AlertDetail()
        body.addWidget(self._detail, 2)
        root.addLayout(body, 1)

        # 兼容旧接口：_toolbar 提供 _level_combo/_node_combo 引用
        from types import SimpleNamespace
        self._level_combo = QComboBox()
        self._level_combo.addItems(["All", "Critical", "Warning"])
        self._level_combo.currentIndexChanged.connect(
            lambda idx: self._set_level([None, "red", "warn"][min(idx, 2)]))
        self._toolbar = SimpleNamespace(
            _level_combo=self._level_combo, _node_combo=self._node_combo)

    # ---- VM ----
    def set_view_model(self, vm):
        self._vm = vm
        if vm:
            vm.alerts_changed.connect(self._refresh_list)
            vm.count_changed.connect(self._refresh_summary)
            self._refresh_summary()
            self._refresh_list()

    def on_show(self):
        super().on_show()
        self._refresh_summary()
        self._refresh_list()
        self._refresh_node_combo()

    # ---- 兼容旧接口 ----
    def _on_filter_changed(self):
        """兼容旧接口：应用当前过滤。"""
        if self._vm:
            level = self._current_level
            self._vm.set_filter_level(level)
            nid = self._node_combo.itemData(self._node_combo.currentIndex())
            self._vm.set_filter_node(nid)
            self._vm.set_search(self._search.text())
            self._refresh_list()

    def update_node_list(self, nodes):
        """外部填充节点下拉（兼容旧接口）。"""
        self._node_combo.blockSignals(True)
        self._node_combo.clear()
        self._node_combo.addItem("全部节点", None)
        for nid, alias in nodes:
            self._node_combo.addItem(alias or nid, nid)
        self._node_combo.blockSignals(False)

    def _card_count(self):
        """当前列表卡片数（统计 AlertEntry）。"""
        cnt = 0
        for i in range(self._list_layout.count()):
            w = self._list_layout.itemAt(i).widget()
            if isinstance(w, AlertEntry):
                cnt += 1
        return cnt

    # ---- 过滤 ----
    def _set_level(self, level):
        self._current_level = level
        for lv, btn in self._level_btns.items():
            btn.setChecked(lv == level)
            btn.setStyleSheet(_chip_style(active=(lv == level)))
        if self._vm:
            self._vm.set_filter_level(level)
            self._refresh_list()

    def _on_node_changed(self, idx):
        if self._vm:
            nid = self._node_combo.itemData(idx)
            self._vm.set_filter_node(nid)
            self._refresh_list()

    def _on_search(self, text):
        if self._vm:
            self._vm.set_search(text)
            self._refresh_list()

    def _on_clear_all(self):
        if self._vm:
            self._vm.clear_all()

    def _refresh_node_combo(self):
        if not self._vm or not self._vm.get_items():
            pass
        self._node_combo.blockSignals(True)
        self._node_combo.clear()
        self._node_combo.addItem("全部节点", None)
        seen = set()
        for item in self._vm.get_items():
            nid = getattr(item, "node_id", None)
            if nid and nid not in seen:
                seen.add(nid)
                alias = getattr(item, "node_alias", "") or nid
                self._node_combo.addItem(alias, nid)
        self._node_combo.blockSignals(False)

    # ---- 刷新 ----
    def _refresh_summary(self):
        if not self._vm:
            return
        self._card_critical.set_value(self._vm.get_red_count(), color=TC.DANGER)
        self._card_warning.set_value(self._vm.get_warn_count(), color=TC.WARNING)
        self._card_active.set_value(self._vm.get_count())
        s = self._vm.get_summary()
        self._card_total.set_value(s.get("total", 0))

    def _refresh_list(self):
        if not self._vm:
            return
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        items = self._vm.get_items()
        if not items:
            lbl = QLabel("暂无告警")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                f"color: {TC.TEXT_DISABLED}; font-size: {TT.BODY_SMALL['size']}px;"
                f" padding: 40px 0; background: transparent;")
            self._empty_label = lbl
            self._list_layout.addWidget(lbl)
            self._list_layout.addStretch(1)
            return
        elif self._empty_label is not None:
            self._empty_label.hide()
        for item in items:
            entry = AlertEntry()
            entry.set_alert(item)
            entry.clicked.connect(self._detail.set_alert)
            self._list_layout.addWidget(entry)
        self._list_layout.addStretch(1)
