# -*- coding: utf-8 -*-
"""
进程采集器（见《README.md》§8.7）。

- 采集频率 2~3 秒，与 1 秒数据帧解耦（process_iter 较重）。
- CPU Top3：psutil.process_iter 排序（需预热）。
- GPU Top3：NVML 取 PID + 占用（见 gpu_collector，P3）。
"""
import logging

import psutil

from node.collectors.base import BaseCollector

log = logging.getLogger("node.collectors.proc")


class ProcCollector(BaseCollector):
    """进程采集器：2.5 秒间隔。"""

    def __init__(self, interval: float = 2.5):
        super().__init__(interval)
        self._prewarmed = False

    def collect(self) -> dict:
        """采集 CPU Top3 进程。"""
        if not self._prewarmed:
            self._prewarmed = True
            for p in psutil.process_iter(["cpu_percent"]):
                try:
                    p.cpu_percent(interval=None)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return {"top_cpu": [], "top_gpu": []}

        procs = []
        for p in psutil.process_iter(["name", "cpu_percent"]):
            try:
                name = p.info.get("name") or "?"
                cpu = p.info.get("cpu_percent") or 0.0
                procs.append((name, cpu))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        procs.sort(key=lambda x: x[1], reverse=True)
        top_cpu = [{"name": n, "usage_percent": round(c, 1)}
                   for n, c in procs[:3]]

        return {
            "top_cpu": top_cpu,
            "top_gpu": [],   # GPU Top3 由 gpu_collector 提供（P3）
        }
