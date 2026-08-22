# -*- coding: utf-8 -*-
"""
NodeTile —— 节点概览卡（v5.5 重设计）。

图标 + 名称 + 状态胶囊 + 3 环形进度（CPU/GPU/RAM）+ 底部指标。
数据来源：DashboardNodeData / DeviceData（有 cpu/gpu/ram/status/alias 等）。
纯 UI，只 import Theme。
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.widgets.glass_card import GlassCard
from host.gui.widgets.ring_gauge import RingGauge
from host.gui.widgets.status_pill import StatusPill


class NodeTile(GlassCard):
    """单节点概览卡，点击发出 node_id。"""

    clicked = pyqtSignal(str)

    def __init__(self, node_id="", alias="", parent=None):
        super().__init__(parent=parent, hover=True, clickable=True)
        self.node_id = node_id
        self._alias = alias
        self._layout.setContentsMargins(S.MD, S.MD, S.MD, S.MD)
        self._layout.setSpacing(S.SM)

        # 头部：图标 + 名称 + 状态
        head = QHBoxLayout()
        head.setSpacing(S.SM)
        self._icon = QLabel("🖥")
        self._icon.setStyleSheet("font-size: 16px; background: transparent;")
        head.addWidget(self._icon)
        self._name_lbl = QLabel(alias)
        self._name_lbl.setStyleSheet(
            f"color: {TC.TEXT_PRIMARY}; font-size: {TT.TITLE_SMALL['size']}px;"
            f" font-weight: 600; background: transparent;")
        head.addWidget(self._name_lbl, 1)
        self._status = StatusPill("connecting")
        head.addWidget(self._status)
        self._layout.addLayout(head)

        # 环形进度行
        rings = QHBoxLayout()
        rings.setSpacing(S.MD)
        self._rings = {}
        self._ring_widgets = {}
        for key, label in [("cpu", "CPU"), ("gpu", "GPU"), ("ram", "RAM")]:
            w = _RingCell(label)
            rings.addWidget(w, 1)
            self._rings[key] = w
            self._ring_widgets[key] = w
        self._layout.addLayout(rings)

        # 底部指标
        self._bottom = QLabel("—")
        self._bottom.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: {TT.CAPTION['size']}px;"
            f" background: transparent;")
        self._layout.addWidget(self._bottom)

        self.node_id = node_id

    def update_data(self, data):
        self._alias = getattr(data, "alias", "") or self.node_id
        status = getattr(data, "status", "connecting")
        self._name_lbl.setText(self._alias)
        self._status.set_status(status)
        # 兼容 DashboardNodeData(cpu_usage) 与 DeviceData(cpu) 两种字段
        self._rings["cpu"].set_value(_get(data, "cpu_usage", "cpu"))
        self._rings["gpu"].set_value(_get(data, "gpu_usage", "gpu"))
        self._rings["ram"].set_value(_get(data, "memory_usage", "ram"))

    def mouseReleaseEvent(self, event):
        self.clicked.emit(self.node_id)
        super().mouseReleaseEvent(event)


class _RingCell(QWidget):
    """环形值单元格：RingGauge + 标签。"""

    def __init__(self, label, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)
        self._gauge = RingGauge()
        layout.addWidget(self._gauge, 0, Qt.AlignCenter)
        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: {TT.CAPTION['size']}px;"
            f" background: transparent;")
        layout.addWidget(lbl)

    def set_value(self, value):
        self._gauge.set_value(value or 0)


def _get(data, *names):
    """从数据对象取第一个存在的属性值，无则 0。"""
    for n in names:
        if hasattr(data, n):
            v = getattr(data, n)
            return v if v is not None else 0
    return 0
