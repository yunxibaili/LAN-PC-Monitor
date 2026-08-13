# -*- coding: utf-8 -*-
"""
AlertsPage —— 告警中心页（v5.2 Phase 3-4B）。

数据流：
  AlertViewModel.alerts_changed → _on_alerts_changed → _refresh_table
  AlertViewModel.count_changed  → _on_count_changed → 更新统计 + SideNav 徽标

约束：
  - 不 import AlertStore / AlertEngine / FrameStore
  - 不 QTimer
  - 纯 Signal 驱动
"""
import logging
import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.pages.base_page import PageBase

log = logging.getLogger("host.gui.alerts_page")


# ---------- 统计卡片 ----------

class _StatCard(QFrame):
    """单个统计数字卡片。"""

    def __init__(self, label: str = "", color: str = TC.TEXT_PRIMARY, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedWidth(120)
        self.setStyleSheet(f"""
            _StatCard {{
                background-color: {TC.BACKGROUND_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 6px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(f"color: {TC.TEXT_DISABLED}; font-size: 11px; background: transparent;")
        layout.addWidget(self._lbl)

        self._val = QLabel("0")
        self._val.setAlignment(Qt.AlignCenter)
        self._val.setStyleSheet(
            f"color: {color}; font-size: 22px; font-weight: bold; background: transparent;")
        layout.addWidget(self._val)

    def set_value(self, value: int) -> None:
        self._val.setText(str(value))


# ---------- AlertsPage ----------

class AlertsPage(PageBase):
    """告警中心页：统计卡片 + 过滤栏 + 告警表格。"""

    PAGE_ID = "alerts"

    _LEVELS = [("全部", None), ("仅红线", "red"), ("仅预警", "warn")]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vm = None
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        # ---- 标题 + 统计卡片 ----
        header = QHBoxLayout()
        header.setSpacing(16)
        title = QLabel("🔔 告警中心")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {TC.TEXT_PRIMARY};")
        header.addWidget(title)
        header.addStretch(1)

        self._card_active = _StatCard("当前告警", TC.ACCENT_PRIMARY)
        self._card_red = _StatCard("红色", TC.STATUS_ERROR)
        self._card_warn = _StatCard("预警", TC.STATUS_WARNING)
        self._card_total = _StatCard("历史总计", TC.TEXT_PRIMARY)
        header.addWidget(self._card_active)
        header.addWidget(self._card_red)
        header.addWidget(self._card_warn)
        header.addWidget(self._card_total)

        self._clear_btn = QPushButton("清除全部")
        self._clear_btn.setFixedHeight(32)
        self._clear_btn.clicked.connect(self._on_clear_all)
        header.addWidget(self._clear_btn)
        root.addLayout(header)

        # ---- 过滤栏 ----
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)

        filter_bar.addWidget(QLabel("等级:"))
        self._level_combo = QComboBox()
        for label, data in self._LEVELS:
            self._level_combo.addItem(label, data)
        self._level_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_bar.addWidget(self._level_combo)

        filter_bar.addWidget(QLabel("节点:"))
        self._node_combo = QComboBox()
        self._node_combo.addItem("所有节点", None)
        self._node_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_bar.addWidget(self._node_combo)

        filter_bar.addWidget(QLabel("搜索:"))
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("告警名 / 指标路径 / 节点别名")
        self._search_box.textChanged.connect(self._on_filter_changed)
        filter_bar.addWidget(self._search_box, 1)

        root.addLayout(filter_bar)

        # ---- 空状态提示 ----
        self._empty_label = QLabel("暂无告警")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: 15px; padding: 40px 0;")
        root.addWidget(self._empty_label)

        # ---- 告警表格 ----
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["时间", "节点", "类型", "指标", "当前值", "阈值", "等级"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {TC.BACKGROUND_PRIMARY};
                alternate-background-color: {TC.TABLE_ALT_ROW};
                gridline-color: {TC.TABLE_GRID};
                color: {TC.TEXT_PRIMARY};
                border: none;
            }}
            QTableWidget::item {{ padding: 4px; }}
            QHeaderView::section {{
                background-color: {TC.TABLE_HEADER_BG};
                color: {TC.TEXT_PRIMARY};
                border: 1px solid {TC.BORDER_DEFAULT};
                padding: 4px;
            }}
        """)
        self._table.hide()  # 空状态时隐藏
        root.addWidget(self._table, 1)

    # ---------- ViewModel 注入 ----------

    def set_view_model(self, vm) -> None:
        """注入 AlertViewModel（MainWindow 调用）。"""
        self._vm = vm
        vm.alerts_changed.connect(self._on_alerts_changed)
        vm.count_changed.connect(self._on_count_changed)

    # ---------- 生命周期 ----------

    def on_show(self) -> None:
        super().on_show()
        self._refresh_table()
        self._refresh_summary()

    def on_hide(self) -> None:
        super().on_hide()

    def cleanup(self) -> None:
        """窗口关闭时断开信号。"""
        if self._vm:
            self._vm.alerts_changed.disconnect(self._on_alerts_changed)
            self._vm.count_changed.disconnect(self._on_count_changed)

    # ---------- 信号回调 ----------

    def _on_alerts_changed(self) -> None:
        """VM 告警列表变化 → 刷新表格 + 统计。"""
        self._refresh_table()
        self._refresh_summary()

    def _on_count_changed(self, count: int) -> None:
        """活动告警数变化 → 更新统计。"""
        self._refresh_summary()

    # ---------- 过滤 ----------

    def _on_filter_changed(self) -> None:
        """过滤条件变化 → 通知 VM 刷新。"""
        if not self._vm:
            return
        level = self._level_combo.currentData()
        node = self._node_combo.currentData()
        self._vm.set_filter_level(level)
        self._vm.set_filter_node(node)
        self._refresh_table()

    def _on_search_changed(self) -> None:
        """搜索框变化。"""
        if self._vm:
            self._vm.set_search(self._search_box.text())
            self._refresh_table()

    def _on_clear_all(self) -> None:
        """清除全部告警。"""
        if self._vm:
            self._vm.clear_all()

    # ---------- 刷新 ----------

    def _refresh_summary(self) -> None:
        """更新统计卡片。"""
        if not self._vm:
            return
        self._card_active.set_value(self._vm.get_count())
        self._card_red.set_value(self._vm.get_red_count())
        self._card_warn.set_value(self._vm.get_warn_count())
        s = self._vm.get_summary()
        self._card_total.set_value(s.get("total", 0))

    def _refresh_table(self) -> None:
        """用 VM.get_items() 重新填充表格。"""
        if not self._vm:
            return
        items = self._vm.get_items()

        if not items:
            self._empty_label.show()
            self._table.hide()
            self._table.setRowCount(0)
            return

        self._empty_label.hide()
        self._table.show()

        # 搜索过滤（VM 已处理 level/node，搜索在 Page 层）
        search = self._search_box.text().strip().lower() if self._search_box else ""
        if search:
            items = [i for i in items
                     if search in (i.name or "").lower()
                     or search in (i.path or "").lower()
                     or search in (i.node_alias or "").lower()]

        self._table.setRowCount(len(items))
        for row, item in enumerate(items):
            ts_str = _fmt_time(item.timestamp)
            self._table.setItem(row, 0, QTableWidgetItem(ts_str))
            self._table.setItem(row, 1, QTableWidgetItem(item.node_alias or ""))
            self._table.setItem(row, 2, QTableWidgetItem(item.name or ""))
            self._table.setItem(row, 3, QTableWidgetItem(item.path or ""))
            self._table.setItem(row, 4, QTableWidgetItem(_fmt_val(item.value)))
            self._table.setItem(row, 5, QTableWidgetItem(_fmt_val(item.threshold)))
            level_item = QTableWidgetItem(item.level.upper())
            if item.level == "red":
                level_item.setForeground(QColor(TC.STATUS_ERROR))
            else:
                level_item.setForeground(QColor(TC.STATUS_WARNING))
            self._table.setItem(row, 6, level_item)

    def update_node_list(self, nodes: list) -> None:
        """更新节点过滤下拉框（MainWindow 调用）。"""
        self._node_combo.clear()
        self._node_combo.addItem("所有节点", None)
        for node_id, alias in nodes:
            self._node_combo.addItem(alias or node_id, node_id)


def _fmt_val(value) -> str:
    """格式化告警值为字符串。"""
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _fmt_time(ts: float) -> str:
    """格式化时间戳为 HH:MM:SS。"""
    if not ts:
        return "--:--:--"
    try:
        import datetime
        return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")
    except (TypeError, ValueError, OSError):
        return "--:--:--"
