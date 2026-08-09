# -*- coding: utf-8 -*-
"""
系统信息采集器（见《README.md》§7 system 字段）。

提供 uptime 与本地 IP。与数据帧一起 1 秒刷新。
"""
import logging
import time

import psutil

from common.utils import get_lan_ip
from node.collectors.base import BaseCollector

log = logging.getLogger("node.collectors.sys")


class SysCollector(BaseCollector):
    """系统信息采集器：1 秒间隔。"""

    def __init__(self, interval: float = 1.0, preferred_iface: str = ""):
        super().__init__(interval)
        self.preferred_iface = preferred_iface

    def collect(self) -> dict:
        """采集系统信息。"""
        boot = None
        try:
            boot = psutil.boot_time()
        except Exception as e:
            log.debug("获取开机时间失败: %s", e)

        uptime = max(0, time.time() - boot) if boot else 0
        return {
            "uptime_seconds": int(uptime),
            "local_ip": get_lan_ip(self.preferred_iface),
        }
