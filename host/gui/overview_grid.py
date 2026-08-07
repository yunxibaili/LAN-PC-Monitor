# -*- coding: utf-8 -*-
"""
监控主机概览网格 —— 同屏展示所有节点关键指标卡片（见《技术文档.md》§18.2）。

单张卡片：3 列 × 2 行，6 项关键指标（CPU/GPU/内存使用率、CPU/GPU 温度、FPS）。
- QGridLayout，每行最多 max_cards_per_row 张（默认 4）。
- 本机节点卡片也参与概览。
- 点击卡片 → 切换到该节点详情视图。
- 数量限制：超过 max_overview_cards 启用横向滚动，显示"共 N 台，显示前 M 台"。
"""
import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                             QScrollArea, QVBoxLayout, QWidget)

from common import theme
from common.theme import apply_color

log = logging.getLogger("host.gui.overview_grid")

MAX_CARDS_PER_ROW = 4


class OverviewCard(QFrame):
    """单个节点的概览卡片。"""

    clicked = pyqtSignal(str)   # node_id

    def __init__(self, node_id: str, alias: str, ip: str, is_local: bool = False):
        super().__init__()
        self.node_id = node_id
        self.alias = alias
        self.ip = ip
        self.is_local = is_local
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            f"OverviewCard {{ background-color: #252526; border: 1px solid #3e3e42;"
            f" border-radius: 6px; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(4)

        head = QHBoxLayout()
        title = QLabel(alias)
        title.setStyleSheet(
            f"font-weight: bold; font-size: 13px; color: {theme.COLOR_TEXT};")
        ip_label = QLabel(ip)
        ip_label.setStyleSheet(f"font-size: 11px; color: {theme.COLOR_NA};")
        head.addWidget(title, 1)
        head.addWidget(ip_label, 0, Qt.AlignRight)
        root.addLayout(head)

        self.status_label = QLabel("● 连接中")
        self.status_label.setStyleSheet(
            f"font-size: 11px; color: {theme.COLOR_WARN};")
        root.addWidget(self.status_label)

        self.metric_labels = {}
        grid = QGridLayout()
        grid.setSpacing(4)
        metrics = [
            ("CPU", "cpu_usage", "%", "usage"),
            ("GPU", "gpu_usage", "%", "usage"),
            ("内存", "ram_usage", "%", "usage"),
            ("CPU温度", "cpu_temp", "°C", "temp"),
            ("GPU温度", "gpu_temp", "°C", "temp"),
            ("FPS", "fps", "", "fps"),
        ]
        for i, (disp, key, unit, kind) in enumerate(metrics):
            row, col = divmod(i, 3)
            cell = QVBoxLayout()
            name = QLabel(disp)
            name.setStyleSheet(f"font-size: 10px; color: {theme.COLOR_NA};")
            value = QLabel("N/A")
            value.setStyleSheet(
                f"font-size: 18px; font-weight: bold; color: {theme.COLOR_NA};")
            cell.addWidget(name)
            cell.addWidget(value)
            grid.addLayout(cell, row, col)
            self.metric_labels[key] = (value, unit, kind)
        root.addLayout(grid)

        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        """点击卡片 → 切换详情视图。"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.node_id)
        super().mousePressEvent(event)

    def update_data(self, summary: dict, status_text: str = "") -> None:
        """用关键指标摘要更新卡片。"""
        if self.is_local:
            color = theme.COLOR_NORMAL
            self.status_label.setText("● 在线")
        else:
            color = (theme.COLOR_NORMAL if "已连接" in status_text
                     else theme.COLOR_WARN if "重连" in status_text
                     else theme.COLOR_DANGER)
            self.status_label.setText(f"● {status_text or '连接中'}")
        self.status_label.setStyleSheet(f"font-size: 11px; color: {color};")

        for key, (label, unit, kind) in self.metric_labels.items():
            value = summary.get(key, "N/A")
            text = "N/A" if value in ("N/A", None) else f"{value}{unit}"
            label.setText(text)
            if kind == "usage":
                apply_color(label, theme.usage_color(value))
            elif kind == "temp":
                apply_color(label, theme.temp_color(value))
            else:
                apply_color(label, theme.COLOR_TEXT)


class OverviewGrid(QScrollArea):
    """概览网格（含横向滚动与数量限制）。"""

    node_clicked = pyqtSignal(str)

    def __init__(self, max_cards_per_row: int = MAX_CARDS_PER_ROW):
        super().__init__()
        self.max_per_row = max_cards_per_row
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        self._grid.setSpacing(12)
        self._grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setWidget(self._container)

        self._cards = {}
        self._count_label = QLabel("")
        self._count_label.setStyleSheet(
            f"font-size: 11px; color: {theme.COLOR_NA};")

    def set_card_limit(self, limit: int) -> None:
        """设置显示卡片上限。"""
        self._limit = limit
        self._refresh_layout()

    def add_card(self, node_id: str, alias: str, ip: str,
                 is_local: bool = False) -> None:
        """添加一张卡片。"""
        if node_id in self._cards:
            return
        card = OverviewCard(node_id, alias, ip, is_local)
        card.clicked.connect(self.node_clicked.emit)
        self._cards[node_id] = card
        self._refresh_layout()

    def remove_card(self, node_id: str) -> None:
        """移除一张卡片。"""
        card = self._cards.pop(node_id, None)
        if card:
            self._grid.removeWidget(card)
            card.deleteLater()
        self._refresh_layout()

    def update_card(self, node_id: str, summary: dict, status_text: str = "") -> None:
        """更新某节点卡片。"""
        card = self._cards.get(node_id)
        if card:
            card.update_data(summary, status_text)

    def _refresh_layout(self) -> None:
        """重排卡片到网格。"""
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w:
                w.hide()

        limit = getattr(self, "_limit", 16)
        visible = list(self._cards.values())[:limit]

        self._count_label.setText(
            f"共 {len(self._cards)} 台，显示前 {len(visible)} 台"
            if len(self._cards) > limit else f"共 {len(self._cards)} 台")
        self._grid.addWidget(self._count_label, 0, 0, 1, self.max_per_row)
        self._count_label.show()

        for idx, card in enumerate(visible):
            row, col = divmod(idx, self.max_per_row)
            self._grid.addWidget(card, row + 1, col)
            card.show()

        for i in range(self.max_per_row):
            self._grid.setColumnStretch(i, 1)
