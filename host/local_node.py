# -*- coding: utf-8 -*-
"""
本机节点 —— 监控主机本地采集（见《技术文档.md》§6.1）。

主机启动时自动在节点列表顶部添加"本机 (localhost)"节点：
- 数据通过本地采集器直接采集（复用 node/collectors/），不经网络。
- 与远程节点同构显示（相同数据结构）。
- 状态始终在线，RTT 固定 0.00ms，不参与重连。
- 不可移除、不可编辑别名。

通过 LocalCollectorPack 聚合本地采集器，1 秒 emit 一帧到 GUI。
"""
import logging
import socket
import threading
import time

from PyQt5.QtCore import QObject, pyqtSignal

from node.collectors import create_collectors, start_all, stop_all

log = logging.getLogger("host.local_node")

# 本机节点固定 ID（§12.2）
LOCAL_NODE_ID = "localhost"


class LocalCollectorPack(QObject):
    """
    本机节点聚合器：1 秒组装本地帧并 emit。

    信号：
        local_data(dict, str) — (monitor_data 帧, LOCAL_NODE_ID)
    """

    local_data = pyqtSignal(dict, str)

    def __init__(self, cfg: dict, interval: float = 1.0):
        super().__init__()
        self.cfg = cfg
        self.interval = interval
        self.collectors = create_collectors(cfg)
        self._stop_event = threading.Event()

    def start(self) -> None:
        """启动采集器与聚合线程。"""
        start_all(self.collectors)
        threading.Thread(target=self._loop, daemon=True,
                         name="local-node-aggregator").start()
        log.info("本机节点已启动")

    def stop(self) -> None:
        """停止本机节点采集。"""
        self._stop_event.set()
        stop_all(self.collectors)

    def _build_frame(self) -> dict:
        """组装本机节点 monitor_data 帧。"""
        frame = {
            "type": "monitor_data",
            "ts": time.time(),
            "hostname": f"{socket.gethostname()} (本机)",
            "connected_clients": 0,
        }
        for section in ("system", "cpu", "ram", "gpu", "net",
                        "net_quality", "fps", "processes"):
            col = self.collectors.get(section)
            frame[section] = col.get() if col else {}
        disk_col = self.collectors.get("disk")
        frame["disk"] = (disk_col.get() or {}).get("disks", []) if disk_col else []
        return frame

    def _loop(self) -> None:
        """每秒 emit 一帧本机数据。"""
        while not self._stop_event.is_set():
            try:
                frame = self._build_frame()
                self.local_data.emit(frame, LOCAL_NODE_ID)
            except Exception as e:
                if self._stop_event.is_set():
                    break
                log.warning("本机节点聚合失败: %s", e)
            self._stop_event.wait(self.interval)
