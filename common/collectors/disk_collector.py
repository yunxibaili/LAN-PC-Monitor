# -*- coding: utf-8 -*-
"""
磁盘采集器（见《README.md》§8.4）。

实现：
- 各盘符读写速度 / IOPS（1 秒差分）。
- 盘符↔物理盘 WMI 映射（增强点 #21）：
  Win32_DiskDriveToDiskPartition + Win32_LogicalDiskToPartition。
- 队列深度：Performance Counter \PhysicalDisk\Current Disk Queue Length。
- 温度：LibreHardwareMonitor（WMI，需管理员），失败 N/A。
- 剩余空间：psutil.disk_usage。

任一环节失败降级 N/A，不抛异常。
"""
import logging
import threading
import time

import psutil

from common.lhm import get_lhm
from common.collectors.base import BaseCollector

# P4: PDH 查询句柄复用（避免每秒 Open/Close Query）
_PDH_QUERY = None      # win32pdh query 句柄
_PDH_COUNTER = None    # win32pdh counter 句柄
_PDH_READY = False

log = logging.getLogger("common.collectors.disk")


class DiskCollector(BaseCollector):
    """磁盘采集器：1 秒间隔。"""

    def __init__(self, interval: float = 1.0):
        super().__init__(interval)
        self._prev_counters = None   # 上一次 per-disk IO 计数
        self._prev_ts = None         # 上一次采样时间
        self._prev_lock = threading.Lock()
        self._map = None             # 盘符 → 物理盘名（WMI 映射，惰性）
        self._lhm = None             # LHM 读取器（惰性）

    # ---------- WMI 盘符↔物理盘映射 ----------

    def _get_drive_map(self) -> dict:
        """
        返回 {盘符(如 "C:"): 物理盘名(如 "PhysicalDrive0")}。
        WMI 不可用时返回空字典（走速度合计兜底）。
        """
        if self._map is not None:
            return self._map
        mapping = {}
        try:
            import wmi
            c = wmi.WMI()
            # Win32_LogicalDiskToPartition: 逻辑盘(盘符) → 分区
            # Win32_DiskDriveToDiskPartition: 物理盘 → 分区
            disk_to_parts = {}
            for assoc in c.Win32_DiskDriveToDiskPartition():
                part = assoc.Antecedent   # Win32_DiskDrive (物理盘)
                part_path = assoc.Dependent  # Win32_DiskPartition (分区)
                disk_name = part.split("=")[-1].strip('"') if part else ""
                disk_to_parts[part_path] = disk_name

            for assoc in c.Win32_LogicalDiskToPartition():
                logical = assoc.Antecedent   # Win32_LogicalDisk (盘符)
                part_path = assoc.Dependent  # Win32_DiskPartition
                drive_letter = ""
                if logical:
                    drive_letter = logical.split('"')[-2] if '"' in logical else ""
                disk_name = disk_to_parts.get(part_path, "")
                if drive_letter and disk_name:
                    mapping[drive_letter] = disk_name
        except Exception as e:
            log.debug("WMI 盘符映射失败: %s", e)
            mapping = {}
        self._map = mapping
        if mapping:
            log.debug("盘符映射: %s", mapping)
        return mapping

    # ---------- IO 差分 ----------

    def _io_speeds(self):
        """计算各物理盘 1 秒差分读写速度与 IOPS。"""
        counters = psutil.disk_io_counters(perdisk=True)
        now = time.monotonic()
        with self._prev_lock:
            prev = self._prev_counters
            prev_ts = self._prev_ts
            self._prev_counters = counters
            self._prev_ts = now

        result = {}
        if prev is None or prev_ts is None:
            return result  # 首次无差分基准，下次才有速度

        dt = now - prev_ts
        if dt <= 0:
            dt = 0.001
        for disk_name, c in counters.items():
            p = prev.get(disk_name)
            if p is None:
                continue
            read_bytes = max(0, c.read_bytes - p.read_bytes)
            write_bytes = max(0, c.write_bytes - p.write_bytes)
            read_ops = max(0, c.read_count - p.read_count)
            write_ops = max(0, c.write_count - p.write_count)
            result[disk_name] = {
                "read_mb_s": round(read_bytes / (1024 ** 2) / dt, 1),
                "write_mb_s": round(write_bytes / (1024 ** 2) / dt, 1),
                "read_iops": int(read_ops / dt),
                "write_iops": int(write_ops / dt),
            }
        return result

    # ---------- 队列深度 ----------

    @staticmethod
    def _queue_depths() -> dict:
        """
        读取物理盘队列深度（Performance Counter，需管理员）。

        P4: PDH 句柄模块级复用（OpenQuery/AddCounter 只做一次），
        后续仅 CollectQueryData 采样，避免每秒 Open/Close 句柄风暴。
        counter 路径使用 raw string，避免 \\P / \\C 转义警告。
        """
        global _PDH_QUERY, _PDH_COUNTER, _PDH_READY
        try:
            import win32pdh
            if not _PDH_READY:
                _PDH_QUERY = win32pdh.OpenQuery()
                path = r"\PhysicalDisk(_Total)\Current Disk Queue Length"
                _PDH_COUNTER = win32pdh.AddCounter(_PDH_QUERY, path)
                _PDH_READY = True
            win32pdh.CollectQueryData(_PDH_QUERY)
            time.sleep(0.05)
            win32pdh.CollectQueryData(_PDH_QUERY)
            _, value = win32pdh.GetFormattedCounterValue(
                _PDH_COUNTER, win32pdh.PDH_FMT_DOUBLE)
            return {"_Total": round(value, 2)}
        except Exception as e:
            log.debug("读取磁盘队列深度失败: %s", e)
            return {}

    # ---------- 采集 ----------

    def collect(self) -> dict:
        """采集磁盘指标：为每个盘符输出一条记录。"""
        speeds = self._io_speeds()
        drive_map = self._get_drive_map()
        queue = self._queue_depths()

        result = []
        for part in psutil.disk_partitions(all=False):
            drive = part.device  # 如 "C:\\"
            mount = part.mountpoint
            if not drive:
                continue

            usage = None
            try:
                usage = psutil.disk_usage(mount or drive)
            except Exception as e:
                log.debug("磁盘 %s 空间获取失败: %s", drive, e)

            drive_label = drive.rstrip("\\/") or drive

            entry = {
                "drive": drive_label,
                "read_mb_s": "N/A",
                "write_mb_s": "N/A",
                "read_iops": 0,
                "write_iops": 0,
                "queue_depth": "N/A",
                "temp_c": "N/A",
                "free_gb": "N/A",
                "total_gb": "N/A",
                "usage_percent": "N/A",
            }

            # 盘符 → 物理盘映射 → IO 速度
            disk_name = drive_map.get(drive_label, "")
            if disk_name and disk_name in speeds:
                entry.update(speeds[disk_name])
            elif speeds:
                entry["read_mb_s"] = round(
                    sum(v["read_mb_s"] for v in speeds.values()), 1)
                entry["write_mb_s"] = round(
                    sum(v["write_mb_s"] for v in speeds.values()), 1)
                entry["read_iops"] = sum(v["read_iops"] for v in speeds.values())
                entry["write_iops"] = sum(v["write_iops"] for v in speeds.values())

            # 队列深度
            qd = queue.get(disk_name) if disk_name else queue.get("_Total")
            if qd is not None:
                entry["queue_depth"] = qd

            # 温度（LHM）
            if self._lhm is None:
                self._lhm = get_lhm()
            if self._lhm.available():
                temp = self._lhm.get_disk_temp(drive_label)
                if temp is not None:
                    entry["temp_c"] = round(temp, 1)

            if usage:
                entry["free_gb"] = round(usage.free / (1024 ** 3), 1)
                entry["total_gb"] = round(usage.total / (1024 ** 3), 1)
                entry["usage_percent"] = round(usage.percent, 1)

            result.append(entry)

        return {"disks": result}
