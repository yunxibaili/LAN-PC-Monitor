# -*- coding: utf-8 -*-
"""
帧率采集器 —— P3 占位（真实实现见《技术文档.md》§10，P4 用 PresentMon + DXGI）。

P3 阶段返回 N/A，保持 §7 Schema 字段完整。
"""
import logging

from node.collectors.base import BaseCollector

log = logging.getLogger("node.collectors.fps")


class FpsCollector(BaseCollector):
    """帧率采集器：P3 占位，2 秒间隔。"""

    def __init__(self, interval: float = 2.0):
        super().__init__(interval)

    def collect(self) -> dict:
        """返回占位字段（P4 用 PresentMon/DXGI 填充）。"""
        return {
            "window_title": "N/A",
            "fps": "N/A",
            "frame_time_ms": "N/A",
            "low_1_percent": "N/A",
            "source": "none",
        }
