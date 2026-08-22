# -*- coding: utf-8 -*-
"""
DeviceCard —— 设备卡片组件（v5.3.4 Devices）。

显示：设备名 + 别名 + 状态徽章 + CPU/RAM/GPU 进度条 + IP + 最后通信时间。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.theme.spacing import ThemeSpacing as S


def _bar_color(val, warn=80, danger=95):
    if val >= danger:
        return TC.BAR_DANGER
    if val >= warn:
        return TC.BAR_WARNING
    return TC.BAR_SUCCESS


class DeviceCard(QFrame):
    """设备卡片。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            DeviceCard {{
                background-color: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
            DeviceCard:hover {{
                border: 1px solid {TC.ACCENT_PRIMARY};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)

        # -- Header: name + status badge --
        header = QHBoxLayout()
        name_col = QVBoxLayout()
        name_col.setSpacing(0)
        self._name = QLabel("")
        self._name.setStyleSheet(
            f"font-size: {TT.TITLE_SMALL['size']}px; font-weight:600; color:{TC.TEXT_PRIMARY};"
            f" background:transparent;")
        self._alias = QLabel("")
        self._alias.setStyleSheet(
            f"font-size: {TT.CAPTION['size']}px; color:{TC.TEXT_SECONDARY}; background:transparent;")
        name_col.addWidget(self._name)
        name_col.addWidget(self._alias)
        header.addLayout(name_col, 1)

        self._badge = QLabel("")
        self._badge.setStyleSheet(
            f"font-size: {TT.CAPTION['size']}px; font-weight:600; padding:3px 10px;"
            f" border-radius:10px; background:transparent;")
        header.addWidget(self._badge)
        layout.addLayout(header)

        # -- Metrics: CPU / RAM / GPU --
        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self._cpu_bar = self._make_metric("CPU")
        self._ram_bar = self._make_metric("RAM")
        self._gpu_bar = self._make_metric("GPU")
        metrics.addLayout(self._cpu_bar["wrap"], 1)
        metrics.addLayout(self._ram_bar["wrap"], 1)
        metrics.addLayout(self._gpu_bar["wrap"], 1)
        layout.addLayout(metrics)

        # -- Footer: IP + last seen --
        footer = QHBoxLayout()
        self._ip = QLabel("")
        self._ip.setStyleSheet(
            f"font-size: {TT.CAPTION['size']}px; color:{TC.TEXT_SECONDARY};"
            f" font-family:Consolas,monospace; background:transparent;")
        footer.addWidget(self._ip)
        footer.addStretch(1)
        self._time = QLabel("")
        self._time.setStyleSheet(
            f"font-size: {TT.CAPTION['size']}px; color:{TC.TEXT_DISABLED}; background:transparent;")
        footer.addWidget(self._time)
        layout.addLayout(footer)

    def _make_metric(self, label):
        wrap = QVBoxLayout()
        wrap.setSpacing(3)
        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"font-size: {TT.CAPTION['size']}px; color:{TC.TEXT_DISABLED};"
            f" font-weight:600; background:transparent;")
        val = QLabel("—")
        val.setStyleSheet(
            f"font-size: {TT.TITLE_SMALL['size']}px; font-weight:700; color:{TC.TEXT_PRIMARY};"
            f" background:transparent;")
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setFixedHeight(4)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{
                border:none; background-color:{TC.BAR_BG}; border-radius:2px;
            }}
            QProgressBar::chunk {{
                border-radius:2px; background-color:{TC.BAR_SUCCESS};
            }}
        """)
        wrap.addWidget(lbl)
        wrap.addWidget(val)
        wrap.addWidget(bar)
        return {"wrap": wrap, "lbl": lbl, "val": val, "bar": bar}

    def update_device(self, device):
        """更新卡片数据（device = DevicesViewModel.DeviceData）。"""
        self._name.setText(device.node_id)
        self._alias.setText(device.alias or "")
        is_online = device.status in ("connected", "online")
        self._set_bar(self._cpu_bar, device.cpu, is_online)
        self._set_bar(self._ram_bar, device.ram, is_online)
        self._set_bar(self._gpu_bar, device.gpu, is_online)

        # Status badge
        if device.status in ("connected", "online"):
            if device.cpu >= 80 or device.ram >= 80:
                self._badge.setText("⚠ Warning")
                self._badge.setStyleSheet(
                    f"font-size: {TT.CAPTION['size']}px; font-weight:600; padding:3px 10px;"
                    f" border-radius:10px; color:{TC.STATUS_WARNING};"
                    f" background:rgba(245,158,11,0.15);")
            else:
                self._badge.setText("● Online")
                self._badge.setStyleSheet(
                    f"font-size: {TT.CAPTION['size']}px; font-weight:600; padding:3px 10px;"
                    f" border-radius:10px; color:{TC.STATUS_ONLINE};"
                    f" background:rgba(34,197,94,0.15);")
        elif device.status in ("timeout", "reconnecting"):
            self._badge.setText("● Connecting")
            self._badge.setStyleSheet(
                f"font-size: {TT.CAPTION['size']}px; font-weight:600; padding:3px 10px;"
                f" border-radius:10px; color:{TC.STATUS_WARNING};"
                f" background:rgba(245,158,11,0.15);")
        else:
            self._badge.setText("● Offline")
            self._badge.setStyleSheet(
                f"font-size: {TT.CAPTION['size']}px; font-weight:600; padding:3px 10px;"
                f" border-radius:10px; color:{TC.STATUS_ERROR};"
                f" background:rgba(239,68,68,0.15);")

        # IP + time
        ip_str = device.ip or ""
        if device.port:
            ip_str += f":{device.port}"
        self._ip.setText(ip_str)
        self._time.setText(device.last_seen_str)

    def _set_bar(self, d, value, is_online):
        d["val"].setText(f"{value:.0f}%")
        if not is_online:
            color = TC.TEXT_DISABLED
            d["val"].setStyleSheet(
                f"font-size: {TT.TITLE_SMALL['size']}px; font-weight:700; color:{color};"
                f" background:transparent;")
            return
        color = _bar_color(value)
        d["val"].setStyleSheet(
            f"font-size: {TT.TITLE_SMALL['size']}px; font-weight:700; color:{color};"
            f" background:transparent;")
        clamped = max(0, min(100, int(value)))
        d["bar"].setValue(clamped)
        d["bar"].setStyleSheet(f"""
            QProgressBar {{
                border:none; background-color:{TC.BAR_BG}; border-radius:2px;
            }}
            QProgressBar::chunk {{
                border-radius:2px; background-color:{color};
            }}
        """)
