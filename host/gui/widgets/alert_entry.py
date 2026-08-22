# -*- coding: utf-8 -*-
"""
AlertEntry —— 告警条目（v5.5 重设计）。

等级色条 + 标题 + 节点/数值/时间。纯 UI，只 import Theme。
"""
import time

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.theme.formatters import format_relative_time
from host.gui.widgets.glass_card import GlassCard


class AlertEntry(GlassCard):
    """单条告警：等级色条 + 标题 + 元信息。"""

    clicked = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent=parent, hover=True, clickable=True)
        self._alert = None
        self._layout.setContentsMargins(S.MD, S.SM, S.MD, S.SM)
        self._layout.setSpacing(S.SM)

        body = QHBoxLayout()
        body.setSpacing(S.MD)
        self._bar = QLabel()
        self._bar.setFixedWidth(3)
        self._bar.setStyleSheet("border-radius: 2px; background: transparent;")
        body.addWidget(self._bar)

        col = QVBoxLayout()
        col.setSpacing(2)
        self._title = QLabel("")
        self._title.setStyleSheet(
            f"color: {TC.TEXT_PRIMARY}; font-size: {TT.BODY_SMALL['size']}px;"
            f" font-weight: 600; background: transparent;")
        col.addWidget(self._title)
        self._meta = QLabel("")
        self._meta.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: {TT.CAPTION['size']}px;"
            f" background: transparent;")
        col.addWidget(self._meta)
        body.addLayout(col, 1)
        self._layout.addLayout(body)

    def set_alert(self, alert):
        self._alert = alert
        level = _field(alert, "level", "warn") or "warn"
        color = TC.alert_color(level)
        self._bar.setStyleSheet(
            f"background: {color}; border-radius: 2px;")
        name = _field(alert, "name", "") or _field(alert, "path", "")
        val = _field(alert, "value", None)
        title = name + (f"  {val:.1f}%" if val is not None else "")
        self._title.setText(title)
        ts = _field(alert, "timestamp", 0)
        alias = _field(alert, "node_alias", "") or _field(alert, "node_id", "") or ""
        ago = format_relative_time(time.time() - ts) if ts else ""
        self._meta.setText(f"{alias} · {ago}".strip(" ·"))

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._alert is not None:
            self.clicked.emit(self._alert)
        super().mouseReleaseEvent(event)


def _field(obj, key, default=None):
    """兼容 dict（.get）与对象（.attr）。"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    if obj is None:
        return default
    v = getattr(obj, key, default)
    return v if v is not None else default
