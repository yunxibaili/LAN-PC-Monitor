# -*- coding: utf-8 -*-
"""
DevicesViewModel —— Devices 页面数据转换层（v5.3.4）。

从 NodeStore + FrameStore 聚合设备列表，对外提供：
  - get_devices() -> [DeviceData]
  - get_summary() -> {online, offline, warning, total}
"""
import time

from host.store.signals import Signal


class DeviceData:
    """单个设备的数据（扁平，UI 直接渲染）。"""
    __slots__ = (
        "node_id", "alias", "ip", "port", "status",
        "cpu", "ram", "gpu", "last_seen", "last_seen_str",
    )

    def __init__(self, node_id="", alias=""):
        self.node_id = node_id
        self.alias = alias
        self.ip = ""
        self.port = 0
        self.status = "connecting"
        self.cpu = 0.0
        self.ram = 0.0
        self.gpu = 0.0
        self.last_seen = 0.0
        self.last_seen_str = ""


class DevicesViewModel:
    """Devices 页面数据转换层。"""

    data_changed = Signal()

    def __init__(self, node_store, frame_store):
        self._ns = node_store
        self._fs = frame_store

        self._ns.node_added.connect(lambda _: self.data_changed.emit())
        self._ns.node_removed.connect(lambda _: self.data_changed.emit())
        self._ns.status_changed.connect(lambda *_: self.data_changed.emit())
        self._fs.frame_updated.connect(lambda *_: self.data_changed.emit())

    def get_devices(self) -> list:
        now = time.time()
        devices = []
        for nid in self._ns.node_ids():
            d = DeviceData(node_id=nid, alias=self._ns.get_alias(nid))
            info = self._ns.get(nid)
            if info:
                d.ip = info.get("ip", "")
                d.port = info.get("port", 0)
            d.status = self._ns.get_status(nid) or "connecting"
            frame = self._fs.get(nid)
            if frame:
                d.cpu = _sf(frame.get("cpu", {}).get("total_usage"))
                d.ram = _sf(frame.get("ram", {}).get("usage_percent"))
                d.gpu = _sf(frame.get("gpu", {}).get("usage_percent"))
            d.last_seen = self._fs.last_seen(nid) or 0.0
            d.last_seen_str = _fmt_ago(now - d.last_seen) if d.last_seen else ""
            devices.append(d)
        return devices

    def get_summary(self) -> dict:
        s = self._ns.summary()
        total = s["total"]
        online = s["online"]
        offline = s["offline"]
        # warning = nodes with connected status but high CPU/RAM
        warning = 0
        for nid in self._ns.node_ids():
            if self._ns.get_status(nid) != "connected":
                continue
            frame = self._fs.get(nid)
            if frame:
                cpu = _sf(frame.get("cpu", {}).get("total_usage"))
                ram = _sf(frame.get("ram", {}).get("usage_percent"))
                if cpu >= 80 or ram >= 80:
                    warning += 1
        return {"online": online, "offline": offline, "warning": warning, "total": total}


def _sf(val, default=0.0):
    if val is None or val == "N/A":
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _fmt_ago(seconds):
    if seconds < 0:
        return "just now"
    if seconds < 5:
        return "just now"
    if seconds < 60:
        return f"{int(seconds)} sec ago"
    if seconds < 3600:
        return f"{int(seconds // 60)} min ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    return f"{int(seconds // 86400)} days ago"
