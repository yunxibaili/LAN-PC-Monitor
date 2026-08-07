# -*- coding: utf-8 -*-
"""
采集节点 TCP Server —— 多监控主机 + 鉴权（见《技术文档.md》§5.4 / §18.4）。

- 监控主机连接后首帧 auth + token，节点校验通过才加入客户端列表。
- 先登记再回 auth_result，避免主机侧计数竞态。
- _ready 集合门控 broadcast：未发完 auth_result 的连接不推送 monitor_data。
- 支持多监控主机同时连接（多主控场景）。
- connected_clients 语义：按主机 IP 去重返回"唯一监控主机数"。
"""
import logging
import socket
import threading

from common.protocol import send_frame, recv_frame

log = logging.getLogger("node.tcp_server")


class MonitorTCPServer:
    """多客户端 TCP 服务器：监听 0.0.0.0:port，广播数据帧。"""

    def __init__(self, host="0.0.0.0", port=12345, token=""):
        self.host = host
        self.port = port
        self.token = token or ""
        self._clients = []        # 已鉴权 TCP 连接列表（用于 broadcast）
        self._peer_ips = set()    # 监控主机唯一 IP 集合（去重计数）
        self._ready = set()       # 已发送 auth_result 的连接（broadcast 只发给这些）
        self._lock = threading.Lock()
        self._running = True
        self._stopping = False

    # ---------- 客户端计数 ----------

    def client_count(self) -> int:
        """TCP 连接数（含同一主机多连接，仅供内部参考）。"""
        with self._lock:
            return len(self._clients)

    def unique_client_count(self) -> int:
        """唯一监控主机数（按 IP 去重），供数据帧 connected_clients 字段。"""
        with self._lock:
            return len(self._peer_ips)

    # ---------- 生命周期 ----------

    def start(self) -> None:
        """启动服务器，accept 循环在独立线程运行。"""
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((self.host, self.port))
        self._server.listen(16)
        threading.Thread(target=self._accept_loop, daemon=True,
                         name="node-tcp-accept").start()
        log.info("TCP Server 已启动 0.0.0.0:%d", self.port)

    def stop(self) -> None:
        """停止服务器并关闭所有客户端连接（退出阶段静默）。"""
        self._running = False
        self._stopping = True
        try:
            self._server.close()
        except Exception:
            pass
        with self._lock:
            for c in self._clients:
                try:
                    c.close()
                except Exception:
                    pass
            self._clients.clear()
            self._peer_ips.clear()
            self._ready.clear()

    def broadcast(self, frame: dict) -> None:
        """
        向所有已鉴权监控主机广播数据帧；失败连接剔除。
        """
        with self._lock:
            clients = [c for c in self._clients if c in self._ready]
        dead = []
        for c in clients:
            try:
                send_frame(c, frame)
            except Exception:
                dead.append(c)
        if dead:
            with self._lock:
                for c in dead:
                    if c in self._clients:
                        self._clients.remove(c)
                    self._ready.discard(c)
                for c in dead:
                    try:
                        peer_ip = c.getpeername()[0]
                    except Exception:
                        continue
                    if peer_ip in self._peer_ips and not any(
                            x.getpeername()[0] == peer_ip for x in self._clients):
                        self._peer_ips.discard(peer_ip)
                    try:
                        c.close()
                    except Exception:
                        pass
            if not self._stopping:
                log.warning("剔除 %d 个失效客户端", len(dead))

    # ---------- 内部实现 ----------

    def _accept_loop(self) -> None:
        """accept 主循环，每客户端一个处理线程。"""
        while self._running:
            try:
                conn, addr = self._server.accept()
            except OSError:
                break
            threading.Thread(target=self._handle, args=(conn, addr),
                             daemon=True, name=f"node-client-{addr[0]}").start()
        log.info("TCP Server 已停止")

    def _handle(self, conn: socket.socket, addr: tuple) -> None:
        """单主机连接处理：鉴权 → 接收 ping/loss_ping → 回 pong。"""
        peer_ip = addr[0]
        conn.settimeout(30)  # 客户端 socket 独立超时
        try:
            auth = recv_frame(conn)
        except Exception:
            auth = None
        if not auth or auth.get("type") != "auth" or auth.get("token") != self.token:
            log.warning("鉴权失败: %s", peer_ip)
            try:
                send_frame(conn, {"type": "auth_result", "ok": False,
                                  "reason": "token错误"})
            except Exception:
                pass
            conn.close()
            return

        # 先登记再回 auth_result，避免主机侧计数竞态
        with self._lock:
            self._clients.append(conn)
            self._peer_ips.add(peer_ip)
        try:
            send_frame(conn, {"type": "auth_result", "ok": True})
            with self._lock:
                self._ready.add(conn)
        except Exception:
            # 客户端在鉴权响应前断开，立即清理
            with self._lock:
                if conn in self._clients:
                    self._clients.remove(conn)
                self._ready.discard(conn)
                self._peer_ips.discard(peer_ip)
            try:
                conn.close()
            except Exception:
                pass
            return
        log.info("监控主机 %s 已连接，当前唯一主机数 %d",
                 peer_ip, self.unique_client_count())

        # --- 接收 ping / loss_ping ---
        try:
            while self._running:
                msg = recv_frame(conn)
                if msg is None:
                    break
                mtype = msg.get("type")
                if mtype == "ping":
                    send_frame(conn, {"type": "pong", "ts": msg["ts"]})
                elif mtype == "loss_ping":
                    send_frame(conn, {"type": "loss_pong",
                                      "seq": msg["seq"], "ts": msg["ts"]})
        except Exception:
            pass
        finally:
            try:
                with self._lock:
                    if conn in self._clients:
                        self._clients.remove(conn)
                    self._ready.discard(conn)
                    if peer_ip in self._peer_ips and not any(
                            c.getpeername()[0] == peer_ip for c in self._clients):
                        self._peer_ips.discard(peer_ip)
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
            if not self._stopping:
                log.info("监控主机 %s 断开，当前唯一主机数 %d",
                         peer_ip, self.unique_client_count())
