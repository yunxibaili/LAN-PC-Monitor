# -*- coding: utf-8 -*-
"""
AlertDetail —— 告警详情面板（v5.2 Phase 4-5）。

选中某条告警后展示完整信息。
纯 UI 组件，无业务逻辑。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S


class AlertDetail(QFrame):
    """告警详情面板：展示单条告警完整信息。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.setFixedHeight(180)
        self.setStyleSheet(f"""
            AlertDetail {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(S.MD, S.SM, S.MD, S.SM)
        layout.setSpacing(S.SM)

        self._title = QLabel("告警详情")
        self._title.setStyleSheet(
            f"color: {TC.TEXT_PRIMARY}; font-size: 14px; font-weight: 600; background: transparent;")
        layout.addWidget(self._title)

        self._fields = {}
        fields = [
            ("severity", "等级"),
            ("name", "告警名称"),
            ("node", "节点"),
            ("path", "指标路径"),
            ("value", "当前值"),
            ("threshold", "阈值"),
            ("time", "时间"),
        ]
        for key, label_text in fields:
            row = QHBoxLayout()
            row.setSpacing(S.SM)
            lbl = QLabel(f"{label_text}:")
            lbl.setFixedWidth(80)
            lbl.setStyleSheet(
                f"color: {TC.TEXT_DISABLED}; font-size: 12px; background: transparent;")
            val = QLabel("—")
            val.setStyleSheet(
                f"color: {TC.TEXT_PRIMARY}; font-size: 12px; background: transparent;")
            row.addWidget(lbl)
            row.addWidget(val, 1)
            layout.addLayout(row)
            self._fields[key] = val

    def set_alert(self, item) -> None:
        """从 AlertItem 展示详情。"""
        self.setVisible(True)
        level = (item.level or "warn").lower()
        sev = "CRITICAL" if level == "red" else "WARNING"
        color = TC.STATUS_ERROR if level == "red" else TC.STATUS_WARNING
        self._fields["severity"].setText(sev)
        self._fields["severity"].setStyleSheet(
            f"color: {color}; font-size: 12px; font-weight: bold; background: transparent;")
        self._fields["name"].setText(item.name or "—")
        self._fields["node"].setText(item.node_alias or item.node_id or "—")
        self._fields["path"].setText(item.path or "—")
        self._fields["value"].setText(str(item.value) if item.value is not None else "—")
        self._fields["threshold"].setText(str(item.threshold) if item.threshold is not None else "—")
        self._fields["time"].setText(_fmt_ts(item.timestamp))

    def clear(self):
        self.setVisible(False)


def _fmt_ts(ts):
    if not ts:
        return "—"
    try:
        import datetime
        return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "—"
