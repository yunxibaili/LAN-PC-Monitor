# -*- coding: utf-8 -*-
"""
DetailDashboard —— 节点详情面板（v5.2 Phase 4-3）。

右侧详情区：NodeHeader + ResourceCards + NetworkCard + ProcessCard。
纯 UI 组件，通过 update_data(data: NodeDetailData) 接收数据。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.widgets.resource_card import ResourceCard
from host.gui.widgets.detail_panel import DetailPanel


class DetailDashboard(QFrame):
    """节点详情仪表盘。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            DetailDashboard {{
                background-color: {TC.BG_SURFACE};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(S.MD, S.SM, S.MD, S.SM)
        layout.setSpacing(S.SM)

        # Node Header
        self._header = QFrame()
        header_layout = QVBoxLayout(self._header)
        header_layout.setContentsMargins(S.LG, S.SM, S.LG, S.SM)
        header_layout.setSpacing(2)

        name_row = QHBoxLayout()
        self._name_lbl = QLabel("未选择节点")
        self._name_lbl.setStyleSheet(f"font-size: TT.TITLE_SMALL['size']px; font-weight: bold; color: {TC.TEXT_PRIMARY}; background: transparent;")
        name_row.addWidget(self._name_lbl)
        name_row.addStretch(1)
        self._status_badge = QLabel("OFFLINE")
        self._status_badge.setStyleSheet(f"background: {TC.TEXT_DISABLED}; color: {TC.TEXT_ON_COLOR}; font-size: TT.CAPTION['size']px; font-weight: 600; padding: 3px 10px; border-radius: 8px;")
        name_row.addWidget(self._status_badge)
        header_layout.addLayout(name_row)

        self._ip_lbl = QLabel("")
        self._ip_lbl.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: TT.BODY_SMALL['size']px; background: transparent;")
        header_layout.addWidget(self._ip_lbl)

        layout.addWidget(self._header)

        # Resource Cards (2x2 grid)
        grid = QGridLayout()
        grid.setSpacing(S.SM)
        self._cpu_card = ResourceCard("CPU", "%")
        self._gpu_card = ResourceCard("GPU", "%")
        self._ram_card = ResourceCard("RAM", "%")
        self._disk_card = ResourceCard("Disk", "%")
        grid.addWidget(self._cpu_card, 0, 0)
        grid.addWidget(self._gpu_card, 0, 1)
        grid.addWidget(self._ram_card, 1, 0)
        grid.addWidget(self._disk_card, 1, 1)
        layout.addLayout(grid)

        # DetailPanel (v5.1 保留，用于完整字段展示)
        self._detail = DetailPanel()
        self._detail.setMaximumHeight(300)
        layout.addWidget(self._detail)

    def update_data(self, data) -> None:
        """从 NodeDetailData 更新。"""
        if data is None:
            self._name_lbl.setText("未选择节点")
            self._detail.clear()
            return
        # Header
        self._name_lbl.setText(data.identity.alias or data.identity.node_id)
        sc = TC.status_color(data.identity.status)
        sm = {"connected": "ONLINE", "offline": "OFFLINE", "connecting": "CONNECTING"}
        self._status_badge.setText(sm.get(data.identity.status, data.identity.status))
        self._status_badge.setStyleSheet(f"background: {sc}; color: {TC.TEXT_ON_COLOR}; font-size: TT.CAPTION['size']px; font-weight: 600; padding: 3px 10px; border-radius: 8px;")
        self._ip_lbl.setText(f"{data.identity.ip}:{data.identity.port}" if data.identity.ip else "")

        # Resource Cards
        self._cpu_card.set_resource(data.cpu.usage or 0, "%", f"{data.cpu.temp_c or 0:.0f}°C" if data.cpu.temp_c else "")
        self._gpu_card.set_resource(data.gpu.usage or 0, "%", f"{data.gpu.core_temp or 0:.0f}°C" if data.gpu.core_temp else "")
        self._ram_card.set_resource(data.memory.usage or 0, "%",
                                     f"{data.memory.used_gb or 0:.1f}/{data.memory.total_gb or 0:.1f}GB")
        self._disk_card.set_resource(data.disk.usage or 0, "%", f"{data.disk.free_gb or 0:.1f}GB free")

        # DetailPanel (v5.1 保持)
        self._detail.update_data(data)
