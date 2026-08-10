# -*- coding: utf-8 -*-
"""
Agent 本机节点 —— 后台服务 + 仪表盘共享的本地采集包（见《README.md》§5.1）。

副机端 Agent 在 --gui 模式下，本进程内弹出仪表盘；仪表盘数据来源于
本模块采集的本地数据帧（不经网络），与推送数据帧格式完全一致（§8）。

与 host.local_node 的关系：
- 两者功能等价（都是"本机节点本地采集"），但分别属于不同角色，互不 import。
- 数据组装格式与 host/local_node.py 保持一致，确保 DetailPanel 可渲染。

与 common.collectors 的关系：
- 直接复用 common/collectors/ 的 create_collectors + 采集器驱动，无重复实现。
"""
import logging
import socket
import threading
import time

from PyQt5.QtCore import QObject, pyqtSignal

from common.collectors import create_collectors, start_all, stop_all

log = logging.getLogger("agent.local_node")

# Agent 本机节点固定 ID（v5.0，§12.2）
LOCAL_NODE_ID = "agent-local"


class LocalCollectorPack(QObject):
    """
    Agent 本机节点聚合器：1 秒组装本地帧并 emit。

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
        self._self_monitor = None

    def start(self) -> None:
        """启动采集器与聚合线程。"""
        start_all(self.collectors)
        threading.Thread(target=self._loop, daemon=True,
                         name="agent-local-aggregator").start()
        # 性能兜底（§15）：本机节点 CPU 超限自动降级（复用 common 实现）
        try:
            from agent.self_monitor import SelfMonitor
            self._self_monitor = SelfMonitor(self, self.collectors)
            self._self_monitor.start()
        except Exception as e:
            log.debug("本机节点自监控启动失败: %s", e)
        log.info("Agent 本机节点已启动")

    def stop(self) -> None:
        """停止本机节点采集。"""
        self._stop_event.set()
        if self._self_monitor:
            self._self_monitor.stop()
        stop_all(self.collectors)

    def _build_frame(self) -> dict:
        """组装本机节点 monitor_data 帧（与 host/local_node.py 同构）。"""
        frame = {
            "type": "monitor_data",
            "ts": time.time(),
            "hostname": f"{socket.gethostname()} (本机 Agent)",
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
