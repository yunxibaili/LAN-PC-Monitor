# -*- coding: utf-8 -*-
"""
采集节点数据聚合器 —— 每 1 秒组装帧并广播（见《技术文档.md》§5.3）。

v3.0：节点不再有本地 GUI 输出，双路输出简化为单路 broadcast。
"""
import logging
import socket
import threading
import time

log = logging.getLogger("node.aggregator")


class DataAggregator:
    """每 1 秒聚合数据，广播给所有已鉴权监控主机。"""

    def __init__(self, server, collectors: dict = None, data_source=None,
                 interval: float = 1.0):
        """
        :param server:     MonitorTCPServer 实例（提供 broadcast 与计数）
        :param collectors: 采集器字典 {"cpu":..., "ram":..., ...}，每项有 get()
        :param data_source: 可选，兼容假数据源（有 make_frame 方法）。
                           传了 data_source 时优先使用，忽略 collectors。
        :param interval:   聚合节拍（秒），自监控降级时可调大
        """
        self.server = server
        self.collectors = collectors or {}
        self.data_source = data_source
        self.interval = interval
        self._stop_event = threading.Event()

    def start(self) -> None:
        """启动聚合线程（daemon）。"""
        threading.Thread(target=self._loop, daemon=True,
                         name="node-aggregator").start()
        log.info("数据聚合器已启动（间隔 %.1fs）", self.interval)

    def stop(self) -> None:
        """停止聚合线程（立即唤醒）。"""
        self._stop_event.set()

    def _build_frame(self) -> dict:
        """从各采集器组装一帧 monitor_data（字段对齐 §7 Schema）。"""
        if self.data_source is not None:
            return self.data_source.make_frame(self.server.unique_client_count())

        frame = {
            "type": "monitor_data",
            "ts": time.time(),
            "hostname": socket.gethostname(),
            "connected_clients": self.server.unique_client_count(),
        }
        for section in ("system", "cpu", "ram", "gpu", "net",
                        "net_quality", "fps", "processes"):
            col = self.collectors.get(section)
            frame[section] = col.get() if col else {}
        disk_col = self.collectors.get("disk")
        frame["disk"] = (disk_col.get() or {}).get("disks", []) if disk_col else []
        return frame

    def _loop(self) -> None:
        """每秒聚合一次并广播。"""
        while not self._stop_event.is_set():
            try:
                frame = self._build_frame()
                self.server.broadcast(frame)
            except Exception as e:
                if self._stop_event.is_set():
                    break
                log.warning("聚合或广播失败: %s", e)
            self._stop_event.wait(self.interval)
