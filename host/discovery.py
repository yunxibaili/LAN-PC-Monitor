# -*- coding: utf-8 -*-
"""
Host 自动发现模块 —— UDP 心跳监听 + mDNS 发现（见《README.md》§2.4 / §20）。

v5.0 前后端分离：
- Host 不再发起 TCP 连接，仅作为发现端监听 Agent 广播。
- 仅依赖 common.utils + zeroconf；不导入 agent/，仅通过协议字段识别。
- 字段兼容：Agent v5.0 心跳含 type=agent_heartbeat / version=5.0；
             旧 v4.0 节点心跳 type=node_heartbeat 也可识别（向下兼容）。
"""
import json
import logging
import socket
import threading
import time

log = logging.getLogger("host.discovery")

# zeroconf 惰性导入；未安装时 mDNS 自动降级
try:
    from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
    _HAS_ZEROCONF = True
except ImportError:
    _HAS_ZEROCONF = False

# mDNS 服务类型（与 Agent 注册一致）
MDNS_SERVICE_TYPE = "_pcmonitor._tcp.local."

# 兼容两种心跳类型
_KNOWN_HEARTBEATS = ("agent_heartbeat", "node_heartbeat")


class DiscoveryListener:
    """UDP 心跳监听器 —— Host 用于自动发现 Agent。"""

    def __init__(self, udp_port: int = 12346, timeout: float = 10.0):
        self.udp_port = udp_port
        self.timeout = timeout
        self._hosts = {}   # ip → {hostname, http_port, token, version, last_seen}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._sock = None

    def start(self) -> None:
        """启动监听线程。"""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("", self.udp_port))
        self._sock.settimeout(1.0)
        threading.Thread(target=self._loop, daemon=True,
                         name="host-udp-listener").start()
        log.info("UDP 心跳监听已启动（端口 %d）", self.udp_port)

    def stop(self) -> None:
        """停止监听。"""
        self._stop_event.set()
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass

    def get_hosts(self) -> dict:
        """返回当前在线节点（按 IP 去重）。"""
        with self._lock:
            return dict(self._hosts)

    def _loop(self) -> None:
        """监听主循环。"""
        while not self._stop_event.is_set():
            try:
                data, addr = self._sock.recvfrom(2048)
            except socket.timeout:
                self._cleanup()
                continue
            except Exception:
                if self._stop_event.is_set():
                    break
                continue
            try:
                msg = json.loads(data.decode("utf-8"))
            except Exception:
                continue
            if msg.get("type") not in _KNOWN_HEARTBEATS:
                continue
            ip = msg.get("ip", addr[0])
            # v5.0 字段优先 http_port，回退 tcp_port（v4.0 兼容）
            port = msg.get("http_port") or msg.get("tcp_port", 0)
            with self._lock:
                self._hosts[ip] = {
                    "hostname": msg.get("hostname", ""),
                    "http_port": port,
                    "tcp_port": port,           # 兼容字段
                    "token": msg.get("token", ""),
                    "version": msg.get("version", "4.0"),
                    "last_seen": time.time(),
                }
        log.info("UDP 心跳监听已停止")

    def _cleanup(self) -> None:
        """清理超时节点。"""
        now = time.time()
        with self._lock:
            stale = [ip for ip, info in self._hosts.items()
                     if now - info["last_seen"] > self.timeout]
            for ip in stale:
                del self._hosts[ip]


class MdnsDiscovery:
    """
    mDNS 零配置发现监听（§23.1）。

    监听 _pcmonitor._tcp.local. 服务，发现 Agent 写入 _hosts。
    与 UDP 心跳并行运行、互为备份；按 ip:port 去重。
    依赖 zeroconf，未安装时自动降级（get_hosts 始终返回空）。
    """

    def __init__(self):
        self._hosts = {}
        self._lock = threading.Lock()
        self._zc = None
        self._listener = None
        self._running = False

    def start(self) -> None:
        """启动 mDNS 监听（zeroconf 不可用时静默降级）。"""
        if not _HAS_ZEROCONF:
            log.info("zeroconf 未安装，mDNS 监听跳过（仅保留 UDP 广播）")
            return
        try:
            outer = self

            class _Listener(ServiceListener):
                def add_service(self, zc, type_, name):
                    outer._on_service(zc, type_, name)

                def remove_service(self, zc, type_, name):
                    outer._on_remove(zc, type_, name)

                def update_service(self, zc, type_, name):
                    outer._on_service(zc, type_, name)

            self._zc = Zeroconf()
            self._listener = _Listener()
            ServiceBrowser(self._zc, MDNS_SERVICE_TYPE, self._listener)
            self._running = True
            log.info("mDNS 监听已启动（%s）", MDNS_SERVICE_TYPE)
        except Exception as e:
            log.warning("mDNS 监听启动失败（自动降级仅 UDP 广播）: %s", e)
            self._zc = None

    def stop(self) -> None:
        """停止 mDNS 监听。"""
        self._running = False
        if self._zc:
            try:
                self._zc.close()
            except Exception:
                pass
            self._zc = None

    def get_hosts(self) -> dict:
        """返回 mDNS 发现的节点（线程安全）。"""
        with self._lock:
            return dict(self._hosts)

    def _on_service(self, zc, type_, name) -> None:
        """发现/更新服务。"""
        try:
            info = zc.get_service_info(type_, name)
            if not info or not info.addresses:
                return
            ip = socket.inet_ntoa(info.addresses[0])
            port = info.port
            hostname = b""
            version = "4.0"
            if info.properties:
                hostname = info.properties.get(b"hostname", b"")
                version_b = info.properties.get(b"version", b"4.0")
                version = version_b.decode("utf-8", errors="replace") \
                    if isinstance(version_b, bytes) else str(version_b)
            if isinstance(hostname, bytes):
                hostname = hostname.decode("utf-8", errors="replace")
            with self._lock:
                self._hosts[ip] = {
                    "hostname": hostname,
                    "http_port": port,
                    "tcp_port": port,           # 兼容字段
                    "token": "",                # mDNS 仅广播 token 摘要
                    "version": version,
                    "mdns": True,
                }
        except Exception as e:
            log.debug("mDNS 服务解析失败: %s", e)

    def _on_remove(self, zc, type_, name) -> None:
        """服务下线：标记离线（不从此处移除，由上层按 §20.9 处理）。"""
        log.debug("mDNS 服务下线: %s", name)


__all__ = [
    "MDNS_SERVICE_TYPE",
    "DiscoveryListener", "MdnsDiscovery",
]
