# -*- coding: utf-8 -*-
"""
内存采集器（见《README.md》§8.2）。

psutil.virtual_memory + swap_memory，最稳定，无额外依赖。
"""
import logging

import psutil

from node.collectors.base import BaseCollector

log = logging.getLogger("node.collectors.ram")


class RamCollector(BaseCollector):
    """内存采集器：1 秒间隔。"""

    def __init__(self, interval: float = 1.0):
        super().__init__(interval)

    def collect(self) -> dict:
        """采集内存指标。"""
        vm = psutil.virtual_memory()
        try:
            swap = psutil.swap_memory()
        except Exception as e:
            log.debug("获取 swap 失败: %s", e)
            swap = None

        return {
            "total_gb": round(vm.total / (1024 ** 3), 2),
            "used_gb": round(vm.used / (1024 ** 3), 2),
            "available_gb": round(vm.available / (1024 ** 3), 2),
            "usage_percent": round(vm.percent, 1),
            "swap_used_mb": round(swap.used / (1024 ** 2), 1) if swap else "N/A",
        }
