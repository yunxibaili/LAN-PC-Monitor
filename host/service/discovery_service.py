# -*- coding: utf-8 -*-
"""
DiscoveryService —— 节点发现服务（v5.2）。

职责（规格）：迁移 `_auto_discover_background` 逻辑，保持现有发现行为。

- 封装现有 host/discovery.py 的 DiscoveryListener（UDP）与 MdnsDiscovery（mDNS）。
- 提供统一合并视图 + 后台自动发现（延迟 + 回调，不阻塞）。
- 不依赖 PyQt5（纯逻辑 + threading）。
"""
import logging
import threading
import time

from host.discovery import DiscoveryListener, MdnsDiscovery

log = logging.getLogger("host.service.discovery")


class DiscoveryService:
    """统一节点发现服务。"""

    def __init__(self, udp_port: int = 12346, auto_start: bool = True):
        self._udp_port = udp_port
        self._listener = DiscoveryListener(udp_port=udp_port)
        self._mdns = MdnsDiscovery()
        self._running = False
        self._stop_event = threading.Event()
        self._thread = None
        self._on_found = None        # 可选回调：found_hosts(dict)
        self._discover_delay = 2.0
        if auto_start:
            self.start()

    # ---------- 生命周期 ----------

    def start(self) -> None:
        """启动两种发现源监听。"""
        if self._running:
            return
        try:
            self._listener.start()
        except Exception as e:
            log.debug("UDP 监听启动失败: %s", e)
        try:
            self._mdns.start()
        except Exception as e:
            log.debug("mDNS 监听启动失败: %s", e)
        self._running = True
        log.info("DiscoveryService 已启动（UDP %d + mDNS）", self._udp_port)

    def stop(self) -> None:
        """停止发现源与后台线程。"""
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        try:
            self._listener.stop()
        except Exception as e:
            log.debug("UDP 监听停止忽略异常: %s", e)
        try:
            self._mdns.stop()
        except Exception as e:
            log.debug("mDNS 停止忽略异常: %s", e)

    # ---------- 发现视图 ----------

    def get_hosts(self) -> dict:
        """合并 UDP + mDNS 发现的节点（按 ip 去重，mDNS 优先保留字段）。"""
        hosts = dict(self._listener.get_hosts())
        for ip, info in self._mdns.get_hosts().items():
            if ip in hosts:
                hosts[ip].update(info)
            else:
                hosts[ip] = info
        return hosts

    def has_hosts(self) -> bool:
        return bool(self.get_hosts())

    # ---------- 后台自动发现（不阻塞） ----------

    def auto_discover_background(self, on_found=None,
                                 delay: float | None = None) -> None:
        """后台延迟执行一次发现，完成后调用 on_found(hosts)。不阻塞。"""
        self._on_found = on_found if on_found is not None else self._on_found
        if delay is not None:
            self._discover_delay = delay
        if self._thread and self._thread.is_alive():
            return
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run_discover,
                                        daemon=True,
                                        name="host-auto-discover")
        self._thread.start()

    def _run_discover(self) -> None:
        """后台线程：等待延迟 → 收集 → 回调。"""
        self._stop_event.wait(self._discover_delay)
        if not self._running:
            return
        try:
            hosts = self.get_hosts()
        except Exception as e:
            log.debug("后台发现失败: %s", e)
            return
        log.info("后台自动发现完成，共发现 %d 个节点", len(hosts))
        if self._on_found:
            try:
                self._on_found(hosts)
            except Exception:
                log.debug("后台发现回调异常", exc_info=True)

    # ---------- 单次扫描（手动"扫描"按钮） ----------

    def scan_once(self, wait: float = 2.0) -> dict:
        """等待并返回当前发现结果。"""
        if not self._running:
            self.start()
        time.sleep(wait)
        return self.get_hosts()
