# -*- coding: utf-8 -*-
"""
监控主机详情面板 —— 单个节点的完整指标展示（见《README.md》§6.3 / §18.3）。

- 分区展示：系统/CPU/内存/GPU/磁盘/网络/网络质量/帧率/进程。
- 阈值变色：使用率/温度/评分/RTT 按 §14.1 变色，N/A 灰色。
- update_all(frame) 由主窗口在每秒数据帧到达时调用（GUI 主线程）。
- get_summary() 提取关键指标供列表项/概览卡片使用。
"""
import logging

from PyQt5.QtWidgets import (QGroupBox, QHBoxLayout, QLabel, QScrollArea,
                             QVBoxLayout, QWidget)

from common import theme
from common.i18n import tr
from common.theme import apply_color
from common.utils import format_uptime

log = logging.getLogger("host.gui.detail_panel")


class DetailPanel(QScrollArea):
    """单个节点的详情面板（可滚动）。"""

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self._build_ui()

    def _build_ui(self) -> None:
        container = QWidget()
        self._root = QVBoxLayout(container)
        self._root.setContentsMargins(8, 8, 8, 8)
        self._root.setSpacing(6)

        self.header_label = QLabel("未连接")
        self.header_label.setObjectName("panel_title")
        self._root.addWidget(self.header_label)

        self._panels = {}
        for title, fields in self._PANEL_FIELDS:
            box, labels = self._make_group(title, fields)
            self._panels[title] = (box, labels)
            self._root.addWidget(box)

        self._root.addStretch(1)
        self.setWidget(container)

    _PANEL_FIELDS = [
        ("cpu.group", [
            ("f.name", "name"), ("f.total_usage", "total_usage"),
            ("f.phys_cores", "physical_cores"), ("f.log_cores", "logical_cores"),
            ("f.freq", "core_freq_mhz"), ("f.temp", "package_temp_c"),
            ("f.power", "power_w"),
        ]),
        ("ram.group", [
            ("f.total", "total_gb"), ("f.used", "used_gb"),
            ("f.available", "available_gb"), ("f.usage", "usage_percent"),
            ("Swap", "swap_used_mb"),
        ]),
        ("gpu.group", [
            ("f.name", "name"), ("f.usage", "usage_percent"),
            ("f.vram_used", "vram_used_mb"), ("f.vram_total", "vram_total_mb"),
            ("f.core_temp", "core_temp_c"), ("f.hotspot_temp", "hotspot_temp_c"),
            ("f.core_freq", "core_freq_mhz"), ("f.power", "power_w"),
        ]),
        ("disk.group", [
            ("f.drive", "drive"), ("f.read", "read_mb_s"), ("f.write", "write_mb_s"),
            ("f.usage", "usage_percent"), ("f.free", "free_gb"),
        ]),
        ("net.group", [
            ("f.iface", "interface"), ("f.up", "upload_mb_s"),
            ("f.down", "download_mb_s"), ("f.link_speed", "link_speed_mbps"),
        ]),
        ("netq.group", [
            ("f.rtt", "latency_to_client_ms"),
            ("f.gw_latency", "latency_to_gateway_ms"),
            ("f.loss", "packet_loss_percent"),
            ("f.score", "quality_score"), ("f.grade", "quality_grade"),
        ]),
        ("fps.group", [
            ("f.window", "window_title"), ("FPS", "fps"),
            ("f.frame_time", "frame_time_ms"), ("f.low1", "low_1_percent"),
            ("f.source", "source"),
        ]),
        ("proc.group", [("f.top", "proc_summary")]),
    ]

    def _make_group(self, title, fields):
        box = QGroupBox(tr(title))
        v = QVBoxLayout(box)
        v.setSpacing(3)
        labels = {}
        for disp, key in fields:
            row = QHBoxLayout()
            name_label = QLabel(tr(disp))
            name_label.setFixedWidth(90)
            value_label = QLabel("N/A")
            value_label.setWordWrap(True)
            row.addWidget(name_label, 0)
            row.addWidget(value_label, 1)
            v.addLayout(row)
            labels[key] = value_label
        return box, labels

    # ---------- 数据更新 ----------

    def update_all(self, frame: dict) -> None:
        """用一帧 monitor_data 更新整个面板。"""
        try:
            self._update_header(frame)
            for key, (_box, labels) in self._panels.items():
                if key == "disk.group":
                    self._update_disk(frame.get("disk", []), labels)
                elif key == "proc.group":
                    self._update_proc(frame.get("processes", {}), labels)
                elif key == "cpu.group":
                    self._update_group(frame.get("cpu", {}), labels,
                                       use_usage_color=True)
                elif key == "ram.group":
                    self._update_group(frame.get("ram", {}), labels,
                                       ram_mode=True)
                elif key == "gpu.group":
                    self._update_group(frame.get("gpu", {}), labels,
                                       gpu_mode=True)
                elif key == "net.group":
                    self._update_group(frame.get("net", {}), labels)
                elif key == "netq.group":
                    self._update_group(frame.get("net_quality", {}), labels,
                                       quality_mode=True)
                elif key == "fps.group":
                    self._update_group(frame.get("fps", {}), labels)
        except Exception as e:
            log.warning("详情面板更新失败: %s", e)

    def _update_header(self, frame: dict) -> None:
        sys_info = frame.get("system", {})
        uptime = format_uptime(sys_info.get("uptime_seconds", 0))
        self.header_label.setText(
            f"{frame.get('hostname', 'N/A')}  |  "
            f"{sys_info.get('local_ip', 'N/A')}  |  {tr('conninfo.header_up', uptime)}")

    def _update_group(self, data: dict, labels: dict, **modes) -> None:
        for key, label in labels.items():
            if label is None:
                continue
            value = data.get(key, "N/A")
            label.setText(_fmt(value))
            apply_color(label, _color_for(key, value, **modes))

    def _update_disk(self, disks: list, labels: dict) -> None:
        if not disks:
            return
        first = disks[0]
        for key, label in labels.items():
            value = first.get(key, "N/A")
            label.setText(_fmt(value))
            apply_color(label, _color_for(key, value))
        names = ", ".join(d.get("drive", "?") for d in disks)
        self._panels["disk.group"][0].setToolTip(f"Drives: {names}")

    def _update_proc(self, processes: dict, labels: dict) -> None:
        label = labels.get("proc_summary")
        if label is None:
            return
        top_cpu = processes.get("top_cpu", [])
        top_gpu = processes.get("top_gpu", [])
        cpu_text = "  ".join(f"{p.get('name','?')} {p.get('usage_percent',0)}%"
                             for p in top_cpu) or "N/A"
        gpu_text = "  ".join(f"{p.get('name','?')} {p.get('usage_percent',0)}%"
                             for p in top_gpu) or "N/A"
        label.setText(f"CPU: {cpu_text}\nGPU: {gpu_text}")
        apply_color(label, theme.COLOR_TEXT)

    # ---------- 关键指标摘要 ----------

    def get_summary(self, frame: dict) -> dict:
        """提取列表项/概览卡片需要的关键指标。"""
        cpu = frame.get("cpu", {})
        gpu = frame.get("gpu", {})
        ram = frame.get("ram", {})
        netq = frame.get("net_quality", {})
        fps = frame.get("fps", {})
        return {
            "cpu_usage": cpu.get("total_usage", "N/A"),
            "gpu_usage": gpu.get("usage_percent", "N/A"),
            "ram_usage": ram.get("usage_percent", "N/A"),
            "cpu_temp": cpu.get("package_temp_c", "N/A"),
            "gpu_temp": gpu.get("core_temp_c", "N/A"),
            "fps": fps.get("fps", "N/A"),
            "rtt": netq.get("latency_to_client_ms", None),
            "score": netq.get("quality_score", "N/A"),
            "grade": netq.get("quality_grade", "N/A"),
        }


def _fmt(value) -> str:
    if value == "N/A" or value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _color_for(key: str, value, use_usage_color=False, ram_mode=False,
               gpu_mode=False, quality_mode=False) -> str:
    if value == "N/A" or value is None:
        return theme.COLOR_NA
    if use_usage_color and key == "total_usage":
        return theme.usage_color(value)
    if ram_mode and key == "usage_percent":
        return theme.usage_color(value)
    if gpu_mode and key in ("usage_percent", "vram_usage_percent"):
        return theme.usage_color(value)
    if key in ("package_temp_c", "core_temp_c", "hotspot_temp_c"):
        return theme.temp_color(value)
    if quality_mode and key == "quality_score":
        return theme.score_color(value)
    if key in ("latency_to_client_ms", "latency_to_gateway_ms"):
        return theme.rtt_color(value)
    if key == "usage_percent" and not ram_mode and not gpu_mode:
        return theme.usage_color(value)
    return theme.COLOR_TEXT
