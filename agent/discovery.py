# -*- coding: utf-8 -*-
"""
Agent 自动发现模块 —— UDP 广播 + mDNS 注册（见《README.md》§2.4 / §20）。

v5.0 重构（前后端分离）：
- Agent 注册端：DiscoveryBroadcaster + register_mdns / unregister_mdns。
- 心跳字段 tcp_port 在 v5.0 改名为 http_port（Agent 的 HTTP/WS 共用端口）。
- Host 监听端（DiscoveryListener、MdnsDiscovery）已迁移到 host/discovery.py。
- 仅依赖 common.utils.get_lan_ip，不再 import node/。
"""
import hashlib
import json
import logging
import socket
import threading
import time

from common.utils import get_lan_ip

log = logging.getLogger("agent.discovery")

# zeroconf 惰性导入；未安装时 mDNS 自动降级（仅 UDP 广播）
try:
    from zeroconf import ServiceInfo, Zeroconf
    _HAS_ZEROCONF = True
except ImportError:
    _HAS_ZEROCONF = False

# mDNS 服务类型（§23.1）
MDNS_SERVICE_TYPE = "_pcmonitor._tcp.local."

# Agent 心跳类型（v5.0，区别于 v4.0 的 node_heartbeat）
HEARTBEAT_TYPE = "agent_heartbeat"


def register_mdns(ip: str, port: int, hostname: str, token: str):
    """
    注册 mDNS 服务（§5.6 / §23.1），供 Host 零配置自动发现。

    返回 Zeroconf 实例（调用方须保持引用）；zeroconf 不可用时返回 None。
    退出时调用 zc.unregister_service() + zc.close()。
    """
    if not _HAS_ZEROCONF:
        log.info("zeroconf 未安装，mDNS 注册跳过（仅保留 UDP 广播）")
        return None
    try:
        service_info = ServiceInfo(
            MDNS_SERVICE_TYPE,
            f"{hostname}.{MDNS_SERVICE_TYPE}",
            addresses=[socket.inet_aton(ip)],
            port=port,
            properties={
                "hostname": hostname,
                "version": "5.0",
                "token_hash": hashlib.sha256(token.encode()).hexdigest()[:8],
            },
        )
        zc = Zeroconf()
        zc.register_service(service_info)
        log.info("mDNS 服务已注册: %s.%s (%s:%d)", hostname, MDNS_SERVICE_TYPE, ip, port)
        return zc
    except Exception as e:
        log.warning("mDNS 注册失败（自动降级仅 UDP 广播）: %s", e)
        return None


def unregister_mdns(zc) -> None:
    """注销 mDNS 服务并关闭 Zeroconf。"""
    if zc is None:
        return
    try:
        zc.close()
    except Exception:
        pass


class DiscoveryBroadcaster:
    """
    Agent UDP 心跳广播器 —— 每 2 秒广播 agent_heartbeat，供 Host 自动发现。

    字段语义（v5.0）：
    - http_port: Agent HTTP/WS 共用端口（v4.0 字段为 tcp_port，v5.0 改名以避免误导）。
    - token: 明文 token（mDNS 走 token_hash，UDP 走明文以兼容旧 host 监听器）。
    """

    def __init__(self, http_port: int, udp_port: int, token: str,
                 interval: float = 2.0, use_multicast: bool = False,
                 preferred_iface: str = ""):
        self.http_port = http_port
        self.udp_port = udp_port
        self.token = token
        self.interval = interval
        self.use_multicast = use_multicast
        self.preferred_iface = preferred_iface
        self._stop_event = threading.Event()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                  socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        if use_multicast:
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    def start(self) -> None:
        """在独立线程启动广播循环。"""
        threading.Thread(target=self._loop, daemon=True,
                         name="agent-udp-broadcast").start()
        log.info("UDP 广播器已启动（%s）",
                 "组播" if self.use_multicast else "广播")

    def stop(self) -> None:
        """停止广播（立即唤醒广播线程）。"""
        self._stop_event.set()
        try:
            self.sock.close()
        except Exception:
            pass

    def _loop(self) -> None:
        """广播主循环。"""
        while not self._stop_event.is_set():
            try:
                lan_ip = get_lan_ip(self.preferred_iface)
                pkt = json.dumps({
                    "type": HEARTBEAT_TYPE,         # v5.0: agent_heartbeat
                    "version": "5.0",
                    "hostname": socket.gethostname(),
                    "ip": lan_ip,
                    "http_port": self.http_port,   # v5.0 字段名
                    "tcp_port": self.http_port,    # 兼容旧 Host 监听器
                    "token_hash": hashlib.sha256(self.token.encode()).hexdigest()[:8],
                    "ts": time.time(),
                }, ensure_ascii=False).encode("utf-8")
                if self.use_multicast:
                    dest = ("239.0.0.1", self.udp_port)
                else:
                    dest = ("<broadcast>", self.udp_port)
                self.sock.sendto(pkt, dest)
            except Exception as e:
                if self._stop_event.is_set():
                    break
                log.warning("UDP 广播失败: %s", e)
            self._stop_event.wait(self.interval)


__all__ = [
    "HEARTBEAT_TYPE", "MDNS_SERVICE_TYPE",
    "register_mdns", "unregister_mdns",
    "DiscoveryBroadcaster",
]
