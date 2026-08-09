# -*- coding: utf-8 -*-
"""
LibreHardwareMonitor (LHM) 温度/功耗读取（见《README.md》§8.1 / §8.4）。

- 通过 WMI 读取 LibreHardwareMonitor 的传感器（需管理员权限）。
- 传感器类型过滤：Temperature / Power / Load 等。
- 任一环节失败返回 None，调用方降级为 N/A，不抛异常。
- 说明：需要本机运行 LibreHardwareMonitor（或其后台库）暴露 WMI 命名空间；
  未安装/未管理员时静默降级。
"""
import logging

log = logging.getLogger("common.lhm")


class LhmReader:
    """LibreHardwareMonitor 传感器读取器（WMI）。"""

    def __init__(self):
        self._wmi = None
        self._init()

    def _init(self) -> None:
        """初始化 WMI 连接（惰性，失败静默）。"""
        try:
            import wmi
            # LibreHardwareMonitor 的 WMI 命名空间
            self._wmi = wmi.WMI(namespace="root\\LibreHardwareMonitor")
        except Exception as e:
            log.debug("LHM WMI 初始化失败（未安装/无管理员权限）: %s", e)
            self._wmi = None

    def available(self) -> bool:
        """LHM 是否可用。"""
        return self._wmi is not None

    def get_sensors(self) -> list:
        """读取所有硬件传感器（失败返回空列表）。"""
        if not self._wmi:
            return []
        try:
            return list(self._wmi.Sensor())
        except Exception as e:
            log.debug("读取 LHM 传感器失败: %s", e)
            return []

    def get_cpu_temp(self) -> float:
        """CPU 封装温度（°C），找不到返回 None。"""
        return self._first_sensor_value("CPU Package", "Temperature")

    def get_cpu_power(self) -> float:
        """CPU 功耗（W），找不到返回 None。"""
        return self._first_sensor_value("CPU Package", "Power")

    def get_disk_temp(self, disk_name: str = "") -> float:
        """磁盘温度（°C），按名称匹配，找不到返回 None。"""
        for s in self.get_sensors():
            if s.SensorType == "Temperature" and "disk" in str(s.Name).lower():
                return _to_float(s.Value)
        return None

    def _first_sensor_value(self, name_fragment: str, sensor_type: str):
        """按名称片段+类型找第一个传感器值。"""
        for s in self.get_sensors():
            if str(s.SensorType) == sensor_type and name_fragment in str(s.Name):
                return _to_float(s.Value)
        return None


def _to_float(value):
    """安全转 float。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# 模块级单例（WMI 连接昂贵，复用）
_lhm = None


def get_lhm() -> LhmReader:
    """获取 LHM 读取器单例。"""
    global _lhm
    if _lhm is None:
        _lhm = LhmReader()
    return _lhm
