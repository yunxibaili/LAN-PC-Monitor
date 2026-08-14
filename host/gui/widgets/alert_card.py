# -*- coding: utf-8 -*-
"""
AlertCard —— 单条告警卡片（v5.2 Phase 4-5）。

展示一条告警的严重度、标题、节点、数值、时间。
纯 UI 组件，无业务逻辑。
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S


class AlertCard(QFrame):
    """告警卡片：severity + title + node + value + timestamp。"""

    clicked = pyqtSignal(object)   # emits AlertItem

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(100)
        self.setStyleSheet(f"""
            AlertCard {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
            AlertCard:hover {{
                border-color: {TC.ACCENT_PRIMARY};
                background-color: {TC.BG_ELEVATED};
            }}
        """)
        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(S.MD, S.SM, S.MD, S.SM)
        root.setSpacing(S.MD)

        # 左侧：严重度色条
        self._severity_bar = QFrame()
        self._severity_bar.setFixedWidth(4)
        self._severity_bar.setStyleSheet(f"background: {TC.TEXT_DISABLED}; border-radius: 2px;")
        root.addWidget(self._severity_bar)

        # 中间：内容
        content = QVBoxLayout()
        content.setSpacing(2)

        top_row = QHBoxLayout()
        top_row.setSpacing(S.SM)
        self._severity_lbl = QLabel("WARN")
        self._severity_lbl.setStyleSheet(
            f"color: {TC.STATUS_WARNING}; font-size: 11px; font-weight: 700; "
            f"letter-spacing: 0.5px; background: transparent;")
        top_row.addWidget(self._severity_lbl)
        top_row.addStretch(1)
        self._time_lbl = QLabel("")
        self._time_lbl.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: 11px; background: transparent;")
        top_row.addWidget(self._time_lbl)
        content.addLayout(top_row)

        self._title_lbl = QLabel("")
        self._title_lbl.setStyleSheet(
            f"color: {TC.TEXT_PRIMARY}; font-size: 14px; font-weight: 600; background: transparent;")
        content.addWidget(self._title_lbl)

        self._node_lbl = QLabel("")
        self._node_lbl.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        content.addWidget(self._node_lbl)

        self._value_lbl = QLabel("")
        self._value_lbl.setStyleSheet(
            f"color: {TC.TEXT_PRIMARY}; font-size: 13px; font-weight: bold; background: transparent;")
        content.addWidget(self._value_lbl)

        root.addLayout(content, 1)

    def set_alert(self, item) -> None:
        """从 AlertItem 填充卡片。"""
        self._item = item

        # 严重度
        level = (item.level or "warn").lower()
        if level == "red":
            sev_text = "CRITICAL"
            sev_color = TC.STATUS_ERROR
            bar_color = TC.STATUS_ERROR
        else:
            sev_text = "WARNING"
            sev_color = TC.STATUS_WARNING
            bar_color = TC.STATUS_WARNING
        self._severity_lbl.setText(sev_text)
        self._severity_lbl.setStyleSheet(
            f"color: {sev_color}; font-size: 11px; font-weight: 700; "
            f"letter-spacing: 0.5px; background: transparent;")
        self._severity_bar.setStyleSheet(f"background: {bar_color}; border-radius: 2px;")

        # 标题
        self._title_lbl.setText(item.name or "Unknown Alert")

        # 节点
        node = item.node_alias or item.node_id or "Unknown"
        self._node_lbl.setText(f"Node: {node}")

        # 数值
        parts = []
        if item.value is not None:
            parts.append(str(item.value))
        if item.threshold is not None:
            parts.append(f"阈值: {item.threshold}")
        self._value_lbl.setText("  |  ".join(parts) if parts else "")

        # 时间
        self._time_lbl.setText(_fmt_time_relative(item.timestamp))

    def mousePressEvent(self, event):
        self.clicked.emit(getattr(self, '_item', None))
        super().mousePressEvent(event)


def _fmt_time_relative(ts: float) -> str:
    """格式化时间为相对时间（如 '2 minutes ago'）。"""
    if not ts:
        return ""
    try:
        import time as _time
        diff = _time.time() - ts
        if diff < 60:
            return "just now"
        elif diff < 3600:
            return f"{int(diff // 60)} minutes ago"
        elif diff < 86400:
            return f"{int(diff // 3600)} hours ago"
        else:
            return f"{int(diff // 86400)} days ago"
    except (TypeError, ValueError):
        return ""
