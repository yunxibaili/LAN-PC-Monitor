# -*- coding: utf-8 -*-
"""
采集节点 UDP 广播器 —— 每 2 秒广播 node_heartbeat 心跳（见《技术文档.md》§4.6 / §5.5）。

心跳类型 v3.0 从 host_heartbeat 改名为 node_heartbeat（§4.2）。
"""
import json
import logging
import socket
import threading
import time

from common.utils import get_lan_ip

log = logging.getLogger("node.discovery")


class DiscoveryBroadcaster:
    """周期性 UDP 广播节点心跳，供监控主机自动发现。"""

    def __init__(self, tcp_port: int, udp_port: int, token: str,
                 interval: float = 2.0, use_multicast: bool = False,
                 preferred_iface: str = ""):
        self.tcp_port = tcp_port
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
                         name="node-udp-broadcast").start()
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
                    "type": "node_heartbeat",   # v3.0 改名（§4.2）
                    "hostname": socket.gethostname(),
                    "ip": lan_ip,
                    "tcp_port": self.tcp_port,
                    "token": self.token,
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


class DiscoveryListener:
    """UDP 心跳监听器 —— 监控主机用于自动发现采集节点（§4.6）。"""

    def __init__(self, udp_port: int = 12346, timeout: float = 10.0):
        self.udp_port = udp_port
        self.timeout = timeout
        self._hosts = {}   # ip → {hostname, tcp_port, token, last_seen}
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
                         name="udp-listener").start()
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
            if msg.get("type") != "node_heartbeat":
                continue
            ip = msg.get("ip", addr[0])
            with self._lock:
                self._hosts[ip] = {
                    "hostname": msg.get("hostname", ""),
                    "tcp_port": msg.get("tcp_port", 0),
                    "token": msg.get("token", ""),
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
