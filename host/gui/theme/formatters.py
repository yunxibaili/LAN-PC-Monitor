# -*- coding: utf-8 -*-
"""
ThemeFormatters —— 统一 UI 数据格式化（v5.2 RC-6）。

所有 UI 组件使用本模块的函数格式化数值，确保一致显示：
- None / "N/A" → "N/A"
- 数值 → 统一精度 + 单位

用法：
    from host.gui.theme.formatters import format_percent, format_temperature
    format_percent(45.2)   # "45.2%"
    format_percent(None)   # "N/A"
    format_temperature(65) # "65°C"
"""


def format_percent(value):
    """格式化百分比（如 CPU/GPU/RAM 使用率）。
    None → "N/A"，45.23 → "45.2%"，0 → "0%"。
    """
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def format_temperature(value):
    """格式化温度（如 CPU/GPU 温度）。
    None → "N/A"，65.0 → "65°C"。
    """
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.0f}°C"
    except (TypeError, ValueError):
        return "N/A"


def format_frequency(value):
    """格式化频率（如 CPU/GPU 核心频率）。
    None → "N/A"，4500 → "4500 MHz"。
    """
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.0f} MHz"
    except (TypeError, ValueError):
        return "N/A"


def format_bytes(value, unit="MB"):
    """格式化字节量（如磁盘读写 / VRAM）。
    None → "N/A"，120.5 → "120.5 MB"。
    """
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.1f} {unit}"
    except (TypeError, ValueError):
        return "N/A"


def format_rtt(value):
    """格式化 RTT 延迟。
    None → "N/A"，0.45 → "0.45 ms"。
    """
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.2f} ms"
    except (TypeError, ValueError):
        return "N/A"


def format_power(value):
    """格式化功耗（如 CPU/GPU 功率）。
    None → "N/A"，65.0 → "65W"。
    """
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.0f}W"
    except (TypeError, ValueError):
        return "N/A"


def format_size_gb(value):
    """格式化 GB 级容量（如内存 / 磁盘剩余）。
    None → "N/A"，45.0 → "45.0 GB"。
    """
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.1f} GB"
    except (TypeError, ValueError):
        return "N/A"
