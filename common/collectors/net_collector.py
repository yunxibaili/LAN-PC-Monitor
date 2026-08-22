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

# P3: 模块级缓存 —— wmi.WMI() 实例复用 + 链路速率 60s 缓存（避免每秒新建 WMI 连接）
_WMI_CACHE = None
_LINK_SPEED_CACHE = {"ts": 0.0, "value": "N/A"}
_LINK_SPEED_TTL = 60.0


def _get_wmi():
    """复用 wmi.WMI() 实例（模块级单例），避免每秒新建连接。"""
    global _WMI_CACHE
    try:
        import wmi
        if _WMI_CACHE is None:
            _WMI_CACHE = wmi.WMI()
        return _WMI_CACHE
    except Exception:
        _WMI_CACHE = None
        return None


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
        """链路速率（Mbps）：WMI Win32_NetworkAdapter，失败返回 N/A。

        P3: wmi 实例复用 + 结果缓存 60s（链路速率变化慢，无需每秒查）。
        """
        now = time.time()
        if now - _LINK_SPEED_CACHE["ts"] < _LINK_SPEED_TTL:
            return _LINK_SPEED_CACHE["value"]
        value = "N/A"
        try:
            c = _get_wmi()
            if c is not None:
                for adapter in c.Win32_NetworkAdapter(NetEnabled=True):
                    if adapter.Name and self._iface and self._iface.lower() in adapter.Name.lower():
                        if adapter.Speed:
                            value = round(int(adapter.Speed) / 1_000_000, 0)
                            break
        except Exception as e:
            log.debug("获取链路速率失败: %s", e)
        _LINK_SPEED_CACHE["ts"] = now
        _LINK_SPEED_CACHE["value"] = value
        return value

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
