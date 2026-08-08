# -*- coding: utf-8 -*-
"""
采集节点 UDP 广播器 —— 每 2 秒广播 node_heartbeat 心跳（见《技术文档.md》§4.6 / §5.5）。

心跳类型 v3.0 从 host_heartbeat 改名为 node_heartbeat（§4.2）。
另含 mDNS 零配置发现注册（§5.6 / §23.1），与 UDP 广播并行、互为备份。
"""
import hashlib
import json
import logging
import socket
import threading
import time

from common.utils import get_lan_ip

log = logging.getLogger("node.discovery")

# zeroconf 惰性导入；未安装时 mDNS 自动降级（仅 UDP 广播）
try:
    from zeroconf import ServiceInfo, Zeroconf
    _HAS_ZEROCONF = True
except ImportError:
    _HAS_ZEROCONF = False

# mDNS 服务类型（§23.1）
MDNS_SERVICE_TYPE = "_pcmonitor._tcp.local."


def register_mdns(ip: str, port: int, hostname: str, token: str):
    """
    注册 mDNS 服务（§5.6 / §23.1），供副机/主机零配置自动发现。

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


class MdnsDiscovery:
    """
    mDNS 零配置发现监听（§23.1）—— 副机/主机端复用。

    启动后自动监听 _pcmonitor._tcp.local. 服务，发现节点写入 _hosts。
    与 UDP 广播心跳并行运行、互为备份；按 ip:port 去重。
    依赖 zeroconf，未安装时自动降级（get_hosts 始终返回空）。

    使用方式（与 DiscoveryListener 一致）：
        mdns = MdnsDiscovery()
        mdns.start()
        nodes = mdns.get_hosts()   # {ip: {"hostname","tcp_port","token","mdns":True}}
        mdns.stop()
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
            from zeroconf import ServiceListener, ServiceBrowser

            class _Listener(ServiceListener):
                def __init__(self, owner):
                    self.owner = owner

                def add_service(self, zc, type_, name):
                    self.owner._on_service(zc, type_, name)

                def remove_service(self, zc, type_, name):
                    self.owner._on_remove(zc, type_, name)

                def update_service(self, zc, type_, name):
                    self.owner._on_service(zc, type_, name)

            self._zc = Zeroconf()
            self._listener = _Listener(self)
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
            if info.properties:
                hostname = info.properties.get(b"hostname", b"")
            if isinstance(hostname, bytes):
                hostname = hostname.decode("utf-8", errors="replace")
            with self._lock:
                self._hosts[ip] = {
                    "hostname": hostname,
                    "tcp_port": port,
                    "token": "",   # mDNS 只广播 token 摘要，完整 token 需接入时确认
                    "mdns": True,
                }
        except Exception as e:
            log.debug("mDNS 服务解析失败: %s", e)

    def _on_remove(self, zc, type_, name) -> None:
        """服务下线：标记离线（不从此处移除，由上层按 §20.9 处理）。"""
        log.debug("mDNS 服务下线: %s", name)
