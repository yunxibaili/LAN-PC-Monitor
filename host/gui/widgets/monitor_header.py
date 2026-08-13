# -*- coding: utf-8 -*-
"""
MonitorHeader —— 监控页头部（v5.2 Phase 4-4）。

显示：节点名称 + 在线状态 + 指标统计信息。
纯 UI 组件，不访问 Store。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S


class MonitorHeader(QFrame):
    """监控页头部：节点名称 + 状态 + 指标摘要。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            MonitorHeader {{
                background-color: {TC.BG_SURFACE};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(S.LG, S.SM, S.LG, S.SM)
        layout.setSpacing(S.MD)

        # 左侧：节点信息
        left = QVBoxLayout()
        left.setSpacing(2)
        node_row = QHBoxLayout()
        node_row.setSpacing(S.SM)
        self._node_lbl = QLabel("未选择节点")
        self._node_lbl.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {TC.TEXT_PRIMARY}; background: transparent;")
        node_row.addWidget(self._node_lbl)
        self._status_badge = QLabel("OFFLINE")
        self._status_badge.setStyleSheet(
            f"background: {TC.TEXT_DISABLED}; color: {TC.TEXT_ON_COLOR}; font-size: 10px; "
            f"font-weight: 600; padding: 3px 10px; border-radius: 8px;")
        node_row.addWidget(self._status_badge)
        node_row.addStretch(1)
        left.addLayout(node_row)

        self._subtitle_lbl = QLabel("选择节点开始监控")
        self._subtitle_lbl.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        left.addWidget(self._subtitle_lbl)

        layout.addLayout(left, 1)

        # 右侧：统计摘要（可选）
        self._stats_row = QHBoxLayout()
        self._stats_row.setSpacing(S.LG)
        self._stats_widgets = {}
        layout.addLayout(self._stats_row)

    def set_node(self, node_id, alias="", status="offline"):
        display = alias if alias else node_id
        self._node_lbl.setText(display if display else "未选择节点")
        sc = TC.status_color(status)
        sm = {"connected": "ONLINE", "offline": "OFFLINE", "connecting": "CONNECTING"}
        self._status_badge.setText(sm.get(status, status.upper()))
        self._status_badge.setStyleSheet(
            f"background: {sc}; color: {TC.TEXT_ON_COLOR}; font-size: 10px; "
            f"font-weight: 600; padding: 3px 10px; border-radius: 8px;")
        self._subtitle_lbl.setText(f"{node_id} · 实时监控")

    def set_stats(self, stats: dict):
        """设置统计摘要: {"points": 120, "metrics": 5, "duration": "2m"}。"""
        # 清除旧的
        while self._stats_row.count():
            item = self._stats_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._stats_widgets.clear()

        for key, value in stats.items():
            w = QFrame()
            w.setStyleSheet(f"background: transparent;")
            vl = QVBoxLayout(w)
            vl.setContentsMargins(0, 0, 0, 0)
            vl.setSpacing(0)
            v_lbl = QLabel(str(value))
            v_lbl.setStyleSheet(
                f"color: {TC.TEXT_PRIMARY}; font-size: 14px; font-weight: bold; background: transparent;")
            v_lbl.setAlignment(Qt.AlignCenter)
            vl.addWidget(v_lbl)
            k_lbl = QLabel(key)
            k_lbl.setStyleSheet(
                f"color: {TC.TEXT_DISABLED}; font-size: 10px; background: transparent;")
            k_lbl.setAlignment(Qt.AlignCenter)
            vl.addWidget(k_lbl)
            self._stats_row.addWidget(w)
            self._stats_widgets[key] = w

    def clear(self):
        self._node_lbl.setText("未选择节点")
        self._subtitle_lbl.setText("选择节点开始监控")
        self._status_badge.setText("OFFLINE")
        self._status_badge.setStyleSheet(
            f"background: {TC.TEXT_DISABLED}; color: {TC.TEXT_ON_COLOR}; font-size: 10px; "
            f"font-weight: 600; padding: 3px 10px; border-radius: 8px;")
        self.set_stats({})
