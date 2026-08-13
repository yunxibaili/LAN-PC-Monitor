# -*- coding: utf-8 -*-
"""
NodeCard —— SaaS 桌面监控卡片（v5.2 Phase 4-2C Visual Polish）。

环形进度 + 状态胶囊 + hover 动画 + 节点图标。
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S


def _draw_arc(painter, cx, cy, radius, value, color):
    """绘制圆弧进度条。"""
    pen = QPen(QColor(color), 4, Qt.SolidLine, Qt.RoundCap)
    painter.setPen(pen)
    span = int(value / 100 * 360 * 16)
    painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2,
                    90 * 16, -span)
    # 背景弧
    painter.setPen(QPen(QColor(TC.BAR_BG), 4, Qt.SolidLine, Qt.RoundCap))
    painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2,
                    90 * 16, -360 * 16)


class NodeCard(QFrame):
    """桌面监控节点卡片：环形进度 + 状态胶囊 + hover 动画。"""

    clicked = pyqtSignal(str)

    def __init__(self, node_id, alias="", parent=None):
        super().__init__(parent)
        self._node_id = node_id
        self._alias = alias
        self._status = "connecting"
        self._cpu = 0.0
        self._gpu = 0.0
        self._ram = 0.0
        self._net_up = 0.0
        self._net_down = 0.0
        self._score = 0
        self._grade = ""
        self._temp = 0.0
        self.setFixedSize(300, 210)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style(TC.BORDER_DEFAULT)
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(S.LG, S.MD, S.LG, S.MD)
        root.setSpacing(3)

        # Header: icon + alias + status badge
        header = QHBoxLayout()
        self._icon = QLabel("🖥")
        self._icon.setStyleSheet(f"font-size: 16px; background: transparent;")
        header.addWidget(self._icon)
        self._alias_lbl = QLabel(self._alias)
        self._alias_lbl.setStyleSheet(
            f"color: {TC.TEXT_PRIMARY}; font-size: 14px; font-weight: 600; background: transparent;")
        header.addWidget(self._alias_lbl, 1)
        self._status_badge = QLabel("OFFLINE")
        self._status_badge.setStyleSheet(
            f"background: {TC.STATUS_OFFLINE}; color: {TC.TEXT_ON_COLOR}; font-size: 9px; "
            f"font-weight: 600; padding: 2px 8px; border-radius: 8px;")
        header.addWidget(self._status_badge)
        root.addLayout(header)

        root.addSpacing(2)

        # Ring progress area: 3 circles side by side
        ring_row = QHBoxLayout()
        ring_row.setSpacing(S.SM)
        self._ring_labels = {}
        self._ring_values = {}
        for name, key in [("CPU", "cpu"), ("GPU", "gpu"), ("RAM", "ram")]:
            rw = QVBoxLayout()
            rw.setSpacing(2)
            rw.setAlignment(Qt.AlignCenter)
            ring_w = QWidget()
            ring_w.setFixedSize(72, 72)
            ring_w.paintEvent = lambda e, k=key: self._paint_ring(e, k)
            rw.addWidget(ring_w, 0, Qt.AlignCenter)
            val = QLabel("—")
            val.setAlignment(Qt.AlignCenter)
            val.setStyleSheet(f"color: {TC.TEXT_PRIMARY}; font-size: 11px; font-weight: bold; background: transparent;")
            rw.addWidget(val)
            self._ring_labels[key] = ring_w
            self._ring_values[key] = val
            ring_row.addLayout(rw)
        ring_row.addStretch(1)
        root.addLayout(ring_row)

        root.addSpacing(2)

        # Bottom metrics: FPS + Temp + Quality
        bottom = QHBoxLayout()
        bottom.setSpacing(S.SM)

        self._fps_lbl = QLabel("FPS --")
        self._fps_lbl.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: 11px; background: transparent;")
        bottom.addWidget(self._fps_lbl)

        self._temp_lbl = QLabel("Temp --")
        self._temp_lbl.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: 11px; background: transparent;")
        bottom.addWidget(self._temp_lbl)

        self._net_lbl = QLabel("↑0 ↓0")
        self._net_lbl.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: 10px; background: transparent;")
        bottom.addWidget(self._net_lbl)

        self._score_lbl = QLabel("Q: --")
        self._score_lbl.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; background: transparent;")
        bottom.addWidget(self._score_lbl)

        root.addLayout(bottom)

    def _paint_ring(self, event, key):
        """绘制环形进度。"""
        painter = QPainter(self._ring_labels[key])
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self._ring_labels[key].width(), self._ring_labels[key].height()
        cx, cy, r = w // 2, h // 2, min(w, h) // 2 - 6
        value = {"cpu": self._cpu, "gpu": self._gpu, "ram": self._ram}.get(key, 0)
        color = {"cpu": TC.SUCCESS, "gpu": TC.ACCENT_PRIMARY, "ram": TC.SUCCESS}.get(key, TC.TEXT_PRIMARY)
        _draw_arc(painter, cx, cy, r, value, color)
        # 中心数字
        painter.setPen(QColor(TC.TEXT_PRIMARY))
        painter.drawText(0, 0, w, h, Qt.AlignCenter, f"{value:.0f}%")

    def update_data(self, data):
        if not data:
            return
        self._alias = data.alias or data.node_id
        self._status = data.status
        self._cpu = data.cpu_usage or 0
        self._gpu = data.gpu_usage or 0
        self._ram = data.memory_usage or 0
        self._net_up = data.network_tx or 0
        self._net_down = data.network_rx or 0
        self._score = data.quality_score or 0
        self._grade = data.quality_grade or ""
        self._refresh()

    def _refresh(self):
        self._alias_lbl.setText(self._alias)
        # Status badge
        sc = TC.status_color(self._status)
        sm = {"connected": "ONLINE", "connecting": "CONNECTING", "reconnecting": "RECONNECTING",
              "offline": "OFFLINE", "auth_failed": "AUTH FAILED"}
        badge_text = sm.get(self._status, self._status)
        self._status_badge.setText(badge_text)
        self._status_badge.setStyleSheet(
            f"background: {sc}; color: {TC.TEXT_ON_COLOR}; font-size: 9px; "
            f"font-weight: 600; padding: 2px 8px; border-radius: 8px;")
        self._apply_style(sc)
        # 环形进度
        self._ring_labels["cpu"].update()
        self._ring_values["cpu"].setText(f"{self._cpu:.0f}%")
        self._ring_labels["gpu"].update()
        self._ring_values["gpu"].setText(f"{self._gpu:.0f}%")
        self._ring_labels["ram"].update()
        self._ring_values["ram"].setText(f"{self._ram:.0f}%")
        # 底部指标
        self._fps_lbl.setText(f"FPS {getattr(self, '_fps', '--')}")
        self._temp_lbl.setText(f"Temp {getattr(self, '_temp', '--')}°C")
        self._net_lbl.setText(f"↑{self._net_up:.1f} ↓{self._net_down:.1f}")
        sc = TC.score_color(self._score)
        self._score_lbl.setText(f"Q: {self._score} {self._grade}")
        self._score_lbl.setStyleSheet(
            f"color: {sc}; font-size: 11px; font-weight: bold; background: transparent;")

    def _apply_style(self, border_color=None):
        bc = border_color or TC.BORDER_DEFAULT
        self.setStyleSheet(f"""
            NodeCard {{
                background-color: {TC.BG_CARD};
                border-left: 3px solid {bc};
                border-top: 1px solid {TC.BORDER_DEFAULT};
                border-right: 1px solid {TC.BORDER_DEFAULT};
                border-bottom: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
            NodeCard:hover {{
                border-left: 3px solid {bc};
                border-top: 1px solid {TC.ACCENT_PRIMARY};
                border-right: 1px solid {TC.ACCENT_PRIMARY};
                border-bottom: 1px solid {TC.ACCENT_PRIMARY};
                background-color: {TC.BG_ELEVATED};
            }}
        """)

    def mousePressEvent(self, event):
        self.clicked.emit(self._node_id)
        super().mousePressEvent(event)
