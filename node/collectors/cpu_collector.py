# -*- coding: utf-8 -*-
"""
CPU 采集器（见《README.md》§8.1）。

实现：型号、总/每核使用率、物理/逻辑核心数、频率。
温度/功耗：LibreHardwareMonitor（WMI，需管理员），失败 N/A。
缓存命中率：Performance Counter，暂 N/A。
"""
import logging

import psutil

try:
    from cpuinfo import get_cpu_info
    _HAS_CPUINFO = True
except ImportError:
    _HAS_CPUINFO = False

from common.lhm import get_lhm
from node.collectors.base import BaseCollector

log = logging.getLogger("node.collectors.cpu")


class CpuCollector(BaseCollector):
    """CPU 采集器：1 秒间隔。"""

    def __init__(self, interval: float = 1.0):
        super().__init__(interval)
        self._prewarmed = False
        self._name = self._get_cpu_name()
        self._lhm = None

    def _get_temp_power(self):
        """从 LHM 读取 CPU 温度与功耗（惰性初始化，失败返回 None）。"""
        if self._lhm is None:
            self._lhm = get_lhm()
        if not self._lhm.available():
            return None, None
        try:
            temp = self._lhm.get_cpu_temp()
            power = self._lhm.get_cpu_power()
            return temp, power
        except Exception as e:
            log.debug("LHM 读 CPU 温度/功耗失败: %s", e)
            return None, None

    @staticmethod
    def _get_cpu_name() -> str:
        """获取 CPU 型号；py-cpuinfo 不可用时返回 N/A。"""
        if _HAS_CPUINFO:
            try:
                return get_cpu_info().get("brand_raw", "N/A") or "N/A"
            except Exception as e:
                log.debug("获取 CPU 型号失败: %s", e)
        return "N/A"

    def collect(self) -> dict:
        """采集 CPU 指标。"""
        if not self._prewarmed:
            self._prewarmed = True
            psutil.cpu_percent(interval=None, percpu=True)
            return self._data or {}

        percpu = psutil.cpu_percent(interval=None, percpu=True)
        total = round(sum(percpu) / len(percpu), 1) if percpu else 0.0

        freq = None
        try:
            freq = psutil.cpu_freq()
        except Exception as e:
            log.debug("获取 CPU 频率失败: %s", e)

        try:
            physical = psutil.cpu_count(logical=False) or 0
        except Exception:
            physical = 0
        try:
            logical = psutil.cpu_count(logical=True) or 0
        except Exception:
            logical = 0

        temp, power = self._get_temp_power()

        return {
            "name": self._name,
            "total_usage": total,
            "per_core_usage": [round(x, 1) for x in percpu],
            "physical_cores": physical,
            "logical_cores": logical,
            "core_freq_mhz": round(freq.current, 1) if freq else "N/A",
            "package_temp_c": round(temp, 1) if temp is not None else "N/A",
            "power_w": round(power, 1) if power is not None else "N/A",
            "l1_hit_rate": "N/A",
            "l2_hit_rate": "N/A",
            "l3_hit_rate": "N/A",
        }
