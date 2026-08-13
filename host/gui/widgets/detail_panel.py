# -*- coding: utf-8 -*-
"""
监控主机详情面板 —— 单个节点的完整指标展示（v5.2 Phase 3-3D）。

数据来源：NodeDetailData（经 NodeDetailViewModel 转换）。
UI 纯展示：不访问 Store，不解析 monitor_data，不保存 node_id。

接口：
    update_data(data: NodeDetailData)  — 用 ViewModel 输出更新
    clear()                             — 清空所有字段
"""
import logging

from PyQt5.QtWidgets import (QGroupBox, QHBoxLayout, QLabel, QScrollArea,
                             QVBoxLayout, QWidget)

from host.gui.theme import (
    COLOR_TEXT, COLOR_NA, usage_color, temp_color, score_color, rtt_color, apply_color,
)
from common.i18n import tr

log = logging.getLogger("host.gui.widgets.detail_panel")


def _fmt(value, fmt=".1f", suffix=""):
    """安全格式化，None 值返回 N/A。"""
    if value is None:
        return "N/A"
    return f"{value:{fmt}}{suffix}"


# 面板字段配置（_build_ui 使用）
_PANEL_FIELDS = [
    ("cpu.group", [
        ("f.name", "name"), ("f.total_usage", "total_usage"),
        ("f.phys_cores", "physical_cores"), ("f.log_cores", "logical_cores"),
        ("f.freq", "core_freq_mhz"), ("f.temp", "package_temp_c"),
        ("f.power", "power_w"),
    ]),
    ("ram.group", [
        ("f.total", "total_gb"), ("f.used", "used_gb"),
        ("f.avail", "available_gb"), ("f.usage", "usage_percent"),
        ("f.swap", "swap_used_mb"),
    ]),
    ("gpu.group", [
        ("f.name", "name"), ("f.usage", "usage_percent"),
        ("f.vram_used", "vram_used_mb"), ("f.vram_total", "vram_total_mb"),
        ("f.core_temp", "core_temp_c"), ("f.hotspot", "hotspot_temp_c"),
        ("f.freq", "core_freq_mhz"), ("f.power", "power_w"),
    ]),
    ("disk.group", [
        ("f drive", "drive"), ("f.read", "read_mb_s"),
        ("f.write", "write_mb_s"), ("f usage", "usage_percent"),
        ("f.free", "free_gb"),
    ]),
    ("net.group", [
        ("f iface", "interface"), ("f.up", "upload_mb_s"),
        ("f.down", "download_mb_s"), ("f.speed", "link_speed_mbps"),
    ]),
    ("net_quality.group", [
        ("f score", "quality_score"), ("f grade", "quality_grade"),
        ("f.rtt_client", "latency_to_client_ms"),
        ("f.rtt_gw", "latency_to_gateway_ms"),
        ("f.loss", "packet_loss_percent"),
    ]),
    ("fps.group", [
        ("f window", "window_title"), ("f.fps", "fps"),
        ("f.frame_time", "frame_time_ms"), ("f.low1", "low_1_percent"),
        ("f.source", "source"),
    ]),
]


class DetailPanel(QScrollArea):
    """详情面板：展示单个节点的完整指标。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self._groups = {}
        self._labels = {}
        self._build_ui()

    def _build_ui(self):
        container = QWidget()
        self.setWidget(container)
        root = QVBoxLayout(container)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        for group_key, fields in _PANEL_FIELDS:
            grp = QGroupBox(tr(group_key))
            layout = QHBoxLayout(grp)
            layout.setSpacing(12)
            for label_key, field in fields:
                col = QVBoxLayout()
                lbl_title = QLabel(tr(label_key))
                lbl_title.setStyleSheet(f"color: {COLOR_NA}; font-size: 11px;")
                col.addWidget(lbl_title)
                lbl_val = QLabel("—")
                lbl_val.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 13px; font-weight: bold;")
                col.addWidget(lbl_val)
                layout.addLayout(col)
                self._labels[field] = lbl_val
            root.addWidget(grp)
            self._groups[group_key] = grp

        root.addStretch(1)

    def update_data(self, data):
        """用 NodeDetailData 更新面板。"""
        if data is None:
            self.clear()
            return
        self._set("name", data.cpu.name)
        self._set("total_usage", f"{data.cpu.usage:.1f}%", usage_color(data.cpu.usage))
        self._set("physical_cores", str(data.cpu.cores_phys or "N/A"))
        self._set("logical_cores", str(data.cpu.cores_logic or "N/A"))
        self._set("core_freq_mhz", f"{_fmt(data.cpu.freq_mhz, '.0f', ' MHz')}")
        self._set("package_temp_c", f"{_fmt(data.cpu.temp_c, '.0f', '°C')}", temp_color(data.cpu.temp_c))
        self._set("power_w", f"{_fmt(data.cpu.power_w, '.0f', 'W')}")

        self._set("total_gb", f"{_fmt(data.memory.total_gb, '.1f', ' GB')}")
        self._set("used_gb", f"{_fmt(data.memory.used_gb, '.1f', ' GB')}")
        self._set("available_gb", f"{_fmt(data.memory.avail_gb, '.1f', ' GB')}")
        self._set("usage_percent", f"{data.memory.usage:.1f}%", usage_color(data.memory.usage))
        self._set("swap_used_mb", f"{_fmt(data.memory.swap_mb, '.0f', ' MB')}")

        self._set("name", data.gpu.name)
        self._set("usage_percent", f"{data.gpu.usage:.1f}%", usage_color(data.gpu.usage))
        self._set("vram_used_mb", f"{_fmt(data.gpu.vram_used, '.0f', ' MB')}")
        self._set("vram_total_mb", f"{_fmt(data.gpu.vram_total, '.0f', ' MB')}")
        self._set("core_temp_c", f"{_fmt(data.gpu.core_temp, '.0f', '°C')}", temp_color(data.gpu.core_temp))
        self._set("hotspot_temp_c", f"{_fmt(data.gpu.hotspot_temp, '.0f', '°C')}", temp_color(data.gpu.hotspot_temp))
        self._set("core_freq_mhz", f"{_fmt(data.gpu.freq_mhz, '.0f', ' MHz')}")
        self._set("power_w", f"{_fmt(data.gpu.power_w, '.0f', 'W')}")

        if data.disk:
            self._set("drive", data.disk.drive)
            self._set("read_mb_s", f"{_fmt(data.disk.read_mb_s, '.1f', ' MB/s')}")
            self._set("write_mb_s", f"{_fmt(data.disk.write_mb_s, '.1f', ' MB/s')}")
            self._set("usage_percent", f"{data.disk.usage:.0f}%", usage_color(data.disk.usage))
            self._set("free_gb", f"{_fmt(data.disk.free_gb, '.1f', ' GB')}")

        self._set("interface", data.network.iface)
        self._set("upload_mb_s", f"{_fmt(data.network.up_mb_s, '.1f', ' MB/s')}")
        self._set("download_mb_s", f"{_fmt(data.network.down_mb_s, '.1f', ' MB/s')}")
        self._set("link_speed_mbps", f"{data.network.link_speed} Mbps")

        self._set("quality_score", str(data.quality.score), score_color(data.quality.score))
        self._set("quality_grade", data.quality.grade)
        self._set("latency_to_client_ms", f"{_fmt(data.quality.rtt, '.2f', ' ms')}")
        self._set("latency_to_gateway_ms", f"{_fmt(data.quality.gw_rtt, '.2f', ' ms')}")
        self._set("packet_loss_percent", f"{_fmt(data.quality.loss, '.1f', '%')}")

        self._set("window_title", data.fps.window)
        self._set("fps", str(data.fps.value))
        self._set("frame_time_ms", f"{_fmt(data.fps.frame_time, '.2f', ' ms')}")
        self._set("low_1_percent", str(data.fps.low1))
        self._set("source", data.fps.source)

    def _set(self, field, text, color=None):
        lbl = self._labels.get(field)
        if lbl is None:
            return
        lbl.setText(str(text))
        if color:
            apply_color(lbl, color)
        else:
            apply_color(lbl, COLOR_TEXT)

    def clear(self):
        for lbl in self._labels.values():
            lbl.setText("—")
            apply_color(lbl, COLOR_TEXT)
