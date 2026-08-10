# -*- coding: utf-8 -*-
"""
网络采集器（见《README.md》§8.5）。

选定主网卡的上行/下行速率（1 秒差分）、链路速率（WMI Win32_NetworkAdapter）、
错误/丢包计数（psutil.net_io_counters）。
"""
import logging
import socket
import threading
import time

import psutil

from common.utils import get_lan_ip
from common.collectors.base import BaseCollector

log = logging.getLogger("common.collectors.net")


class NetCollector(BaseCollector):
    """网络采集器：1 秒间隔。"""

    def __init__(self, interval: float = 1.0, preferred_iface: str = ""):
        super().__init__(interval)
        self.preferred_iface = preferred_iface
        self._iface = self._pick_interface()
        self._prev_state = (None, None, None)
        self._prev_lock = threading.Lock()

    def _pick_interface(self) -> str:
        """选取主网卡：优先与 get_lan_ip 结果一致的网卡。"""
        try:
            lan_ip = get_lan_ip(self.preferred_iface)
            for iface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and addr.address == lan_ip:
                        return iface
        except Exception as e:
            log.debug("网卡选取失败: %s", e)
        return ""

    def _link_speed(self) -> object:
        """链路速率（Mbps）：WMI Win32_NetworkAdapter，失败返回 N/A。"""
        try:
            import wmi
            c = wmi.WMI()
            for adapter in c.Win32_NetworkAdapter(NetEnabled=True):
                if adapter.Name and self._iface and self._iface.lower() in adapter.Name.lower():
                    if adapter.Speed:
                        return round(int(adapter.Speed) / 1_000_000, 0)
            return "N/A"
        except Exception as e:
            log.debug("获取链路速率失败: %s", e)
            return "N/A"

    def collect(self) -> dict:
        """采集网络指标。"""
        pernic = psutil.net_io_counters(pernic=True)
        aggregate = psutil.net_io_counters()
        now = time.monotonic()
        with self._prev_lock:
            prev_pernic, prev_agg, prev_ts = self._prev_state
            self._prev_state = (pernic, aggregate, now)

        if self._iface and self._iface in pernic:
            c = pernic[self._iface]
            p = prev_pernic.get(self._iface) if prev_pernic else None
            iface_name = self._iface
        else:
            c = aggregate
            p = prev_agg if prev_agg is not None else None
            iface_name = self._iface or "全部接口"

        upload = download = 0.0
        err_s = err_r = drop_s = drop_r = 0
        if p is not None:
            dt = (now - prev_ts) if prev_ts else 0
            if dt <= 0:
                dt = 0.001
            upload = max(0, c.bytes_sent - p.bytes_sent) / (1024 ** 2) / dt
            download = max(0, c.bytes_recv - p.bytes_recv) / (1024 ** 2) / dt
            err_s, err_r = c.errout, c.errin
            drop_s, drop_r = c.dropout, c.dropin

        return {
            "interface": iface_name,
            "upload_mb_s": round(upload, 2),
            "download_mb_s": round(download, 2),
            "link_speed_mbps": self._link_speed(),
            "errors_sent": err_s,
            "errors_recv": err_r,
            "drops_sent": drop_s,
            "drops_recv": drop_r,
        }
