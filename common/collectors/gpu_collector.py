# -*- coding: utf-8 -*-
"""
GPU 采集器（见《README.md》§8.3）。

NVIDIA：pynvml 全指标（使用率/显存/温度/频率/功耗/功耗墙/引擎细分/显存进程）。
AMD：pyadl 后备（仅使用率/温度/频率，其余 N/A）。
Intel：降级 N/A。
无 GPU 或库不可用：全 N/A，不报错。

GPU Top3 进程（§8.3.4）：NVML nvmlDeviceGetComputeRunningProcesses 取 PID
→ psutil.Process(pid).name()。注意 usedGpuMemory 可能为 None，必须判空跳过。
"""
import logging

import psutil

from common.lhm import get_lhm
from common.collectors.base import BaseCollector

log = logging.getLogger("common.collectors.gpu")

# pynvml 惰性导入，避免无 NVIDIA 环境报错
try:
    import pynvml
    _HAS_NVML = True
except ImportError:
    _HAS_NVML = False

# pyadl 惰性导入（AMD 后备）
# 注意：pyadl 在无 AMD 驱动时于 import 阶段直接 raise ADLError("Driver not found!")
# （非 ImportError），因此必须捕获 Exception 而非仅 ImportError，
# 否则非 AMD 机器上 import 本模块即崩溃（CI 实测：Agent 启动秒退）。
try:
    from pyadl import ADLManager
    _HAS_ADL = True
except Exception:  # noqa: BLE001 — 导入失败即视为无 ADL，降级 N/A
    _HAS_ADL = False


class GpuCollector(BaseCollector):
    """GPU 采集器：2 秒间隔。"""

    def __init__(self, interval: float = 2.0, gpu_index: int = 0):
        super().__init__(interval)
        self._backend = "none"
        self._nvml_initialized = False
        self.gpu_index = gpu_index  # 多 GPU 时指定主卡 index（§8.3.1）
        self._init_gpu()

    # ---------- 初始化 ----------

    def _init_gpu(self) -> None:
        """探测可用 GPU 后端（NVML → ADL → none）。"""
        if _HAS_NVML:
            try:
                pynvml.nvmlInit()
                self._nvml_initialized = True
                count = pynvml.nvmlDeviceGetCount()
                if count > 0:
                    self._backend = "nvml"
                    log.info("GPU 后端: NVML（%d 张 NVIDIA 显卡）", count)
                    return
            except Exception as e:
                log.warning("NVML 初始化失败: %s", e)
        if _HAS_ADL:
            try:
                ADLManager.getInstance()
                self._backend = "adl"
                log.info("GPU 后端: ADL（AMD）")
                return
            except Exception as e:
                log.warning("ADL 初始化失败: %s", e)
        log.info("GPU 后端: 无（Intel 或未安装 pynvml/pyadl，GPU 区 N/A）")
        self._backend = "none"

    def stop(self) -> None:
        """停止采集并关闭 NVML。"""
        super().stop()
        if self._nvml_initialized:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass
            self._nvml_initialized = False

    # ---------- 采集 ----------

    def collect(self) -> dict:
        """采集 GPU 指标。"""
        if self._backend == "nvml":
            return self._collect_nvml()
        if self._backend == "adl":
            return self._collect_adl()
        return self._na_dict()

    def _na_dict(self) -> dict:
        """全 N/A 字段（Intel / 无 GPU）。"""
        return {
            "name": "N/A",
            "usage_percent": "N/A",
            "vram_used_mb": "N/A",
            "vram_total_mb": "N/A",
            "vram_usage_percent": "N/A",
            "core_temp_c": "N/A",
            "mem_temp_c": "N/A",
            "hotspot_temp_c": "N/A",
            "core_freq_mhz": "N/A",
            "mem_freq_mhz": "N/A",
            "power_w": "N/A",
            "power_limit_w": "N/A",
            "engine_usage": "N/A",
            "top_vram_processes": [],
        }

    # ---------- NVML 采集 ----------

    def _collect_nvml(self) -> dict:
        """NVIDIA pynvml 全指标采集。"""
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(self.gpu_index)
            name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode("utf-8", errors="replace")

            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            usage = round(util.gpu, 1)

            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            vram_used = round(mem.used / (1024 ** 2))
            vram_total = round(mem.total / (1024 ** 2))
            vram_pct = round(vram_used / vram_total * 100, 1) if vram_total else 0.0

            temp = None
            try:
                temp = pynvml.nvmlDeviceGetTemperature(
                    handle, pynvml.NVML_TEMPERATURE_GPU)
            except Exception:
                pass

            core_freq = None
            mem_freq = None
            try:
                core_freq = pynvml.nvmlDeviceGetClockInfo(
                    handle, pynvml.NVML_CLOCK_GRAPHICS)
            except Exception:
                pass
            try:
                mem_freq = pynvml.nvmlDeviceGetClockInfo(
                    handle, pynvml.NVML_CLOCK_MEM)
            except Exception:
                pass

            power_w = None
            power_limit_w = None
            try:
                power_w = round(pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0, 1)
            except Exception:
                pass
            try:
                power_limit_w = round(
                    pynvml.nvmlDeviceGetEnforcedPowerLimit(handle) / 1000.0, 1)
            except Exception:
                pass

            engine = self._engine_usage(handle)
            top_procs = self._top_vram_processes(handle)

            return {
                "name": name,
                "usage_percent": usage,
                "vram_used_mb": vram_used,
                "vram_total_mb": vram_total,
                "vram_usage_percent": vram_pct,
                "core_temp_c": temp if temp is not None else "N/A",
                "mem_temp_c": self._mem_temp(handle),
                "hotspot_temp_c": self._hotspot_temp(handle),
                "core_freq_mhz": core_freq if core_freq is not None else "N/A",
                "mem_freq_mhz": mem_freq if mem_freq is not None else "N/A",
                "power_w": power_w if power_w is not None else "N/A",
                "power_limit_w": power_limit_w if power_limit_w is not None else "N/A",
                "engine_usage": engine,
                "top_vram_processes": top_procs,
            }
        except Exception as e:
            log.warning("NVML 采集失败: %s", e)
            return self._na_dict()

    @staticmethod
    def _engine_usage(handle) -> dict:
        """
        引擎使用率细分：graphics/compute/encode/decode（§8.3.1）。
        graphics 与 usage_percent 同源；encode/decode 用 NVML 专用 API。
        """
        try:
            overall = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
        except Exception:
            overall = 0.0
        # encode/decode：返回 (utilization%, sampling_period_us)，取第一项
        encode = decode = 0.0
        try:
            encode = pynvml.nvmlDeviceGetEncoderUtilization(handle)[0]
        except Exception:
            pass
        try:
            decode = pynvml.nvmlDeviceGetDecoderUtilization(handle)[0]
        except Exception:
            pass
        return {
            "graphics": round(overall, 1),
            "compute": round(overall, 1),
            "encode": round(encode, 1),
            "decode": round(decode, 1),
        }

    @staticmethod
    def _mem_temp(handle):
        """
        显存温度（部分卡支持，§9.3.1）。
        用 getattr 判断 NVML_TEMPERATURE_MEMORY 枚举是否存在，避免
        旧版 nvidia-ml-py 属性缺失导致采集失败。
        """
        ntype = getattr(pynvml, "NVML_TEMPERATURE_MEMORY", None)
        if ntype is None:
            return "N/A"
        try:
            t = pynvml.nvmlDeviceGetTemperature(handle, ntype)
            return round(t, 1)
        except Exception:
            return "N/A"

    def _hotspot_temp(self, handle):
        """
        热点温度（§9.3.1 回退链路）：
        1. 优先 NVML NVML_TEMPERATURE_GPU_HOTSPOT（getattr 判断枚举存在性）
        2. 不可用 → 回退 LibreHardwareMonitor WMI 补读（需管理员）
        3. 再不可用 → "N/A"
        """
        ntype = getattr(pynvml, "NVML_TEMPERATURE_GPU_HOTSPOT", None)
        if ntype is not None:
            try:
                t = pynvml.nvmlDeviceGetTemperature(handle, ntype)
                return round(t, 1)
            except Exception:
                pass  # API 存在但调用失败，继续走 LHM 回退
        # 回退：LHM WMI 读取 GPU 热点温度（需管理员）
        try:
            lhm = get_lhm()
            if lhm.available():
                for s in lhm.get_sensors():
                    if str(s.SensorType) == "Temperature" and \
                            "gpu" in str(s.Name).lower() and \
                            ("hotspot" in str(s.Name).lower() or
                             "junction" in str(s.Name).lower()):
                        return round(float(s.Value), 1)
        except Exception as e:
            log.debug("LHM 补读 GPU 热点温度失败: %s", e)
        return "N/A"

    @staticmethod
    def _top_vram_processes(handle) -> list:
        """显存占用 Top3 进程（§8.3.4：usedGpuMemory 判空跳过）。"""
        try:
            procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
        except Exception:
            try:
                procs = pynvml.nvmlDeviceGetGraphicsRunningProcesses(handle)
            except Exception:
                return []
        result = []
        for p in procs:
            pid = int(p.pid)
            # 关键健壮性：新版 nvidia-ml-py ≥13 usedGpuMemory 可能为 None，
            # 判空跳过，否则 None / 1024**2 抛 TypeError 导致整个 GPU 采集失败。
            mem = getattr(p, "usedGpuMemory", None)
            if mem is None:
                continue
            vram_mb = round(mem / (1024 ** 2))
            name = "?"
            try:
                name = psutil.Process(pid).name()
            except Exception:
                pass
            result.append({"name": name, "vram_mb": vram_mb})
        result.sort(key=lambda x: x["vram_mb"], reverse=True)
        return result[:3]

    # ---------- ADL 采集（AMD 后备） ----------

    def _collect_adl(self) -> dict:
        """
        AMD pyadl 有限指标采集（§9.3.2：仅使用率/温度/频率真实，其余 N/A）。
        pyadl 多年未更新，API 可能随驱动失效；用 getattr 防御各字段。
        """
        try:
            dev = ADLManager.getInstance().getDevices()[0]
            name = getattr(dev, "getName", None)
            name = name() if name else "AMD GPU"
            # usage / temp / 频率均可能缺失，逐字段防御
            try:
                usage = round(dev.getCurrentUsage(), 1)
            except Exception:
                usage = "N/A"
            try:
                temp = dev.getCurrentTemperature()
            except Exception:
                temp = "N/A"
            try:
                core_freq = dev.getCurrentEngineClock()
            except Exception:
                core_freq = "N/A"
            try:
                mem_freq = dev.getCurrentMemoryClock()
            except Exception:
                mem_freq = "N/A"
            return {
                "name": name,
                "usage_percent": usage,
                "vram_used_mb": "N/A",
                "vram_total_mb": "N/A",
                "vram_usage_percent": "N/A",
                "core_temp_c": temp,
                "mem_temp_c": "N/A",
                "hotspot_temp_c": "N/A",
                "core_freq_mhz": core_freq,
                "mem_freq_mhz": mem_freq,
                "power_w": "N/A",
                "power_limit_w": "N/A",
                "engine_usage": "N/A",
                "top_vram_processes": [],
            }
        except Exception as e:
            log.warning("ADL 采集失败: %s", e)
            return self._na_dict()
