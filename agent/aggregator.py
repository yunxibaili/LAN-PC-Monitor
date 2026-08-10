# -*- coding: utf-8 -*-
"""
Agent 数据聚合器 —— 每 1 秒组装 monitor_data 帧并写入最新帧缓存（见《README.md》§5.3）。

v5.0：不再像 v4.0 节点那样由聚合器直接 broadcast；改为写入线程安全的
"最新帧缓存"，WebSocket 推送协程从缓存读取广播。这样 REST/WS/仪表盘
都能取到同一份最新帧，解耦聚合与推送。
"""
import logging
import socket
import threading
import time

log = logging.getLogger("agent.aggregator")


class DataAggregator:
    """每 1 秒聚合数据，写入最新帧缓存。"""

    def __init__(self, collectors: dict = None, data_source=None,
                 interval: float = 1.0):
        """
        :param collectors: 采集器字典 {"cpu":..., "ram":..., ...}，每项有 get()
        :param data_source: 可选，兼容假数据源（有 make_frame 方法）。
                           传了 data_source 时优先使用，忽略 collectors。
        :param interval:   聚合节拍（秒），自监控降级时可调大
        """
        self.collectors = collectors or {}
        self.data_source = data_source
        self.interval = interval
        self._latest = {}                # 最新帧缓存
        self._lock = threading.Lock()    # 保护 _latest
        self._stop_event = threading.Event()
        self._subscriber_counter = None  # 订阅者计数回调（由 main 注入）

    # ---------- 对外接口 ----------

    def latest_frame(self) -> dict:
        """返回最新一帧的副本（线程安全）。"""
        with self._lock:
            return dict(self._latest)

    def connected_clients(self) -> int:
        """当前 WS 订阅者数。由 main 注入的计数回调设置；无则返回 0。"""
        if self._subscriber_counter is not None:
            try:
                return self._subscriber_counter()
            except Exception:
                return 0
        return 0

    def set_subscriber_counter(self, fn) -> None:
        """注入订阅者计数回调（agent.main 中绑定到 ws_server）。"""
        self._subscriber_counter = fn

    # ---------- 生命周期 ----------

    def start(self) -> None:
        """启动聚合线程（daemon）。"""
        threading.Thread(target=self._loop, daemon=True,
                         name="agent-aggregator").start()
        log.info("数据聚合器已启动（间隔 %.1fs）", self.interval)

    def stop(self) -> None:
        """停止聚合线程（立即唤醒）。"""
        self._stop_event.set()

    # ---------- 内部实现 ----------

    def _build_frame(self) -> dict:
        """从各采集器组装一帧 monitor_data（字段对齐 §7 Schema）。"""
        if self.data_source is not None:
            return self.data_source.make_frame(self.connected_clients())

        frame = {
            "type": "monitor_data",
            "ts": time.time(),
            "hostname": socket.gethostname(),
            "connected_clients": self.connected_clients(),
        }
        for section in ("system", "cpu", "ram", "gpu", "net",
                        "net_quality", "fps", "processes"):
            col = self.collectors.get(section)
            frame[section] = col.get() if col else {}
        disk_col = self.collectors.get("disk")
        frame["disk"] = (disk_col.get() or {}).get("disks", []) if disk_col else []
        return frame

    def _loop(self) -> None:
        """每秒聚合一次并写入缓存。"""
        while not self._stop_event.is_set():
            try:
                frame = self._build_frame()
                with self._lock:
                    self._latest = frame
            except Exception as e:
                if self._stop_event.is_set():
                    break
                log.warning("聚合失败: %s", e)
            self._stop_event.wait(self.interval)
