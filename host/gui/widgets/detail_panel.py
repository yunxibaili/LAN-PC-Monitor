# -*- coding: utf-8 -*-
"""
监控主机详情面板 —— 单个节点的完整指标展示（v5.2 Phase 3-3D / RC-6 修复）。

数据来源：NodeDetailData（经 NodeDetailViewModel 转换）。
UI 纯展示：不访问 Store，不解析 monitor_data，不保存 node_id。

接口：
    update_data(data: NodeDetailData)  — 用 ViewModel 输出更新
    clear()                             — 清空所有字段

RC-6 修复：字段键加组前缀消除 CPU/GPU/RAM/Disk 命名冲突。
"""
import logging

from PyQt5.QtWidgets import (QGroupBox, QHBoxLayout, QLabel, QScrollArea,
                             QVBoxLayout, QWidget)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme import usage_color, temp_color, score_color, rtt_color, apply_color
from common.i18n import tr

log = logging.getLogger("host.gui.widgets.detail_panel")

# 字段键规范（RC-6）：
# 所有字段键采用 {组}_{字段} 前缀命名，消除跨组同名冲突。
# 禁止使用裸字段名（如 name / usage_percent / core_freq_mhz / power_w）。
_PANEL_FIELDS = [
    ("cpu.group", [
        ("f.name", "cpu_name"), ("f.total_usage", "cpu_usage"),
        ("f.phys_cores", "cpu_cores_phys"), ("f.log_cores", "cpu_cores_logic"),
        ("f.freq", "cpu_freq_mhz"), ("f.temp", "cpu_temp_c"),
        ("f.power", "cpu_power_w"),
    ]),
    ("ram.group", [
        ("f.total", "ram_total_gb"), ("f.used", "ram_used_gb"),
        ("f.avail", "ram_avail_gb"), ("f.usage", "ram_usage"),
        ("f.swap", "ram_swap_mb"),
    ]),
    ("gpu.group", [
        ("f.name", "gpu_name"), ("f.usage", "gpu_usage"),
        ("f.vram_used", "gpu_vram_used"), ("f.vram_total", "gpu_vram_total"),
        ("f.core_temp", "gpu_core_temp"), ("f.hotspot", "gpu_hotspot_temp"),
        ("f.freq", "gpu_freq_mhz"), ("f.power", "gpu_power_w"),
    ]),
    ("disk.group", [
        ("f.drive", "disk_drive"), ("f.read", "disk_read"),
        ("f.write", "disk_write"), ("f usage", "disk_usage"),
        ("f.free", "disk_free"),
    ]),
    ("net.group", [
        ("f iface", "net_interface"), ("f.up", "net_upload"),
        ("f.down", "net_download"), ("f.speed", "net_speed"),
    ]),
    ("net_quality.group", [
        ("f score", "quality_score"), ("f grade", "quality_grade"),
        ("f.rtt_client", "quality_rtt_client"),
        ("f.rtt_gw", "quality_rtt_gw"),
        ("f.loss", "quality_loss"),
    ]),
    ("fps.group", [
        ("f window", "fps_window"), ("f.fps", "fps_value"),
        ("f.frame_time", "fps_frame_time"), ("f.low1", "fps_low1"),
        ("f.source", "fps_source"),
    ]),
]


def _fmt(value, fmt=".1f", suffix=""):
    """安全格式化，None 值返回 N/A。"""
    if value is None:
        return "N/A"
    return f"{value:{fmt}}{suffix}"


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
                lbl_title.setStyleSheet(f"color: {TC.TEXT_DISABLED}; font-size: TT.CAPTION['size']px;")
                col.addWidget(lbl_title)
                lbl_val = QLabel("—")
                lbl_val.setStyleSheet(f"color: {TC.TEXT_PRIMARY}; font-size: TT.BODY['size']px; font-weight: bold;")
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

        # CPU（组前缀 cpu_）
        self._set("cpu_name", data.cpu.name)
        self._set("cpu_usage", f"{_fmt(data.cpu.usage, '.1f', '%')}", usage_color(data.cpu.usage))
        self._set("cpu_cores_phys", str(data.cpu.cores_phys or "N/A"))
        self._set("cpu_cores_logic", str(data.cpu.cores_logic or "N/A"))
        self._set("cpu_freq_mhz", f"{_fmt(data.cpu.freq_mhz, '.0f', ' MHz')}")
        self._set("cpu_temp_c", f"{_fmt(data.cpu.temp_c, '.0f', '°C')}", temp_color(data.cpu.temp_c))
        self._set("cpu_power_w", f"{_fmt(data.cpu.power_w, '.0f', 'W')}")

        # RAM（组前缀 ram_）
        self._set("ram_total_gb", f"{_fmt(data.memory.total_gb, '.1f', ' GB')}")
        self._set("ram_used_gb", f"{_fmt(data.memory.used_gb, '.1f', ' GB')}")
        self._set("ram_avail_gb", f"{_fmt(data.memory.avail_gb, '.1f', ' GB')}")
        self._set("ram_usage", f"{_fmt(data.memory.usage, '.1f', '%')}", usage_color(data.memory.usage))
        self._set("ram_swap_mb", f"{_fmt(data.memory.swap_mb, '.0f', ' MB')}")

        # GPU（组前缀 gpu_）
        self._set("gpu_name", data.gpu.name)
        self._set("gpu_usage", f"{_fmt(data.gpu.usage, '.1f', '%')}", usage_color(data.gpu.usage))
        self._set("gpu_vram_used", f"{_fmt(data.gpu.vram_used, '.0f', ' MB')}")
        self._set("gpu_vram_total", f"{_fmt(data.gpu.vram_total, '.0f', ' MB')}")
        self._set("gpu_core_temp", f"{_fmt(data.gpu.core_temp, '.0f', '°C')}", temp_color(data.gpu.core_temp))
        self._set("gpu_hotspot_temp", f"{_fmt(data.gpu.hotspot_temp, '.0f', '°C')}", temp_color(data.gpu.hotspot_temp))
        self._set("gpu_freq_mhz", f"{_fmt(data.gpu.freq_mhz, '.0f', ' MHz')}")
        self._set("gpu_power_w", f"{_fmt(data.gpu.power_w, '.0f', 'W')}")

        # Disk（组前缀 disk_）
        if data.disk:
            self._set("disk_drive", data.disk.drive)
            self._set("disk_read", f"{_fmt(data.disk.read_mb_s, '.1f', ' MB/s')}")
            self._set("disk_write", f"{_fmt(data.disk.write_mb_s, '.1f', ' MB/s')}")
            self._set("disk_usage", f"{_fmt(data.disk.usage, '.0f', '%')}", usage_color(data.disk.usage))
            self._set("disk_free", f"{_fmt(data.disk.free_gb, '.1f', ' GB')}")

        # Network（组前缀 net_）
        self._set("net_interface", data.network.iface)
        self._set("net_upload", f"{_fmt(data.network.up_mb_s, '.1f', ' MB/s')}")
        self._set("net_download", f"{_fmt(data.network.down_mb_s, '.1f', ' MB/s')}")
        self._set("net_speed", f"{data.network.link_speed} Mbps")

        # Quality（组前缀 quality_）
        self._set("quality_score", str(data.quality.score), score_color(data.quality.score))
        self._set("quality_grade", data.quality.grade)
        self._set("quality_rtt_client", f"{_fmt(data.quality.rtt, '.2f', ' ms')}")
        self._set("quality_rtt_gw", f"{_fmt(data.quality.gw_rtt, '.2f', ' ms')}")
        self._set("quality_loss", f"{_fmt(data.quality.loss, '.1f', '%')}")

        # FPS（组前缀 fps_）
        self._set("fps_window", data.fps.window)
        self._set("fps_value", str(data.fps.value))
        self._set("fps_frame_time", f"{_fmt(data.fps.frame_time, '.2f', ' ms')}")
        self._set("fps_low1", str(data.fps.low1))
        self._set("fps_source", data.fps.source)

    def _set(self, field, text, color=None):
        lbl = self._labels.get(field)
        if lbl is None:
            return
        lbl.setText(str(text))
        if color:
            apply_color(lbl, color)
        else:
            apply_color(lbl, TC.TEXT_PRIMARY)

    def clear(self):
        for lbl in self._labels.values():
            lbl.setText("—")
            apply_color(lbl, TC.TEXT_PRIMARY)
