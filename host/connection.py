# -*- coding: utf-8 -*-
"""
监控主机单节点连接器 —— NodeConnection（见《README.md》§6.2 / §4.7）。

- 独立连接线程：连接 → 鉴权 → 阻塞接收；断线独立指数退避重连（1s→60s）。
- socket 独立超时 30s。
- RTT 测量：每 1 秒发 ping，节点回 pong，主机 perf_counter 计算 RTT。
- 丢包测量（§4.5）：每 5 秒发 3 个 loss_ping，1 秒后统计丢包率。
- 所有信号带 node_id，GUI 按 node_id 路由。
"""
import logging
import socket
import threading
import time

from PyQt5.QtCore import QObject, pyqtSignal

from common.protocol import send_frame, recv_frame

log = logging.getLogger("host.connection")

# 丢包测量参数（§4.5）
LOSS_INTERVAL = 5.0
LOSS_BATCH = 3
LOSS_SPACING = 0.1
LOSS_WAIT = 1.0


class NodeConnection(QObject):
    """
    单个采集节点的连接对象。

    信号：
        data_received(dict, str)  — (monitor_data 帧, node_id)
        status_changed(str, str)  — (状态文本, node_id)
        rtt_updated(float, str)   — (rtt_ms, node_id)
        loss_updated(float, str)  — (丢包率%, node_id)
    """

    data_received = pyqtSignal(dict, str)
    status_changed = pyqtSignal(str, str)
    rtt_updated = pyqtSignal(float, str)
    loss_updated = pyqtSignal(float, str)

    def __init__(self, node_id: str, ip: str, port: int, token: str, alias: str = ""):
        super().__init__()
        self.node_id = node_id
        self.ip = ip
        self.port = port
        self.token = token or ""
        self.alias = alias or f"{ip}:{port}"
        self._sock = None
        self._running = True
        self._stop_event = threading.Event()
        self._connected = False
        # 丢包统计状态
        self._loss_lock = threading.Lock()
        self._loss_pending = {}
        self._loss_last = 0.0
        # 日志带 node_id 标签（§11.2）
        self.log = logging.getLogger(f"host.node.{node_id}")

    # ---------- 生命周期 ----------

    def start(self) -> None:
        """启动连接线程（daemon）。"""
        threading.Thread(target=self._connect_loop, daemon=True,
                         name=f"node-conn-{self.node_id}").start()

    def stop(self) -> None:
        """停止连接并关闭 socket（stop 驱动断开静默）。"""
        self._stop_event.set()
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass

    def is_connected(self) -> bool:
        return self._connected

    # ---------- 连接主循环 ----------

    def _connect_loop(self) -> None:
        """连接 + 指数退避重连循环。"""
        backoff = 1
        while self._running and not self._stop_event.is_set():
            try:
                self._sock = socket.create_connection(
                    (self.ip, self.port), timeout=5)
                self._sock.settimeout(30)

                # 鉴权：连接后首帧 auth
                send_frame(self._sock, {"type": "auth", "token": self.token})
                auth = recv_frame(self._sock)
                if not auth or not auth.get("ok"):
                    reason = (auth or {}).get("reason", "unknown error")
                    self._emit_status("auth_failed")
                    self.log.warning("%s 鉴权失败: %s", self.alias, reason)
                    self._sock.close()
                    self._sock = None
                    self._stop_event.wait(backoff)
                    backoff = min(backoff * 2, 60)
                    continue

                self._connected = True
                backoff = 1
                self._emit_status("connected")
                self.log.info("%s 已连接", self.alias)

                threading.Thread(target=self._ping_loop, daemon=True,
                                 name=f"node-ping-{self.node_id}").start()
                threading.Thread(target=self._loss_loop, daemon=True,
                                 name=f"node-loss-{self.node_id}").start()

                self._recv_loop()  # 阻塞直到断开

                self._connected = False
                if self._stop_event.is_set():
                    break
                self._emit_status("reconnecting")
                self.log.info("%s 断开", self.alias)

            except socket.timeout:
                self._connected = False
                if self._stop_event.is_set():
                    break
                self._emit_status("timeout")
            except Exception as e:
                self._connected = False
                if self._stop_event.is_set():
                    break
                self._emit_status("offline")
                self.log.warning("%s 连接失败: %s", self.alias, e)
            finally:
                if self._sock:
                    try:
                        self._sock.close()
                    except Exception:
                        pass
                    self._sock = None

            if not self._running or self._stop_event.is_set():
                break
            self._stop_event.wait(backoff)
            backoff = min(backoff * 2, 60)

    # ---------- 接收循环 ----------

    def _recv_loop(self) -> None:
        """阻塞接收帧，分发给对应信号。"""
        while self._running and self._sock and not self._stop_event.is_set():
            try:
                frame = recv_frame(self._sock)
            except Exception:
                break
            if frame is None:
                break
            t = frame.get("type")
            if t == "monitor_data":
                self.data_received.emit(frame, self.node_id)
            elif t == "pong":
                rtt = (time.perf_counter() - frame["ts"]) * 1000
                self.rtt_updated.emit(rtt, self.node_id)
            elif t == "loss_pong":
                seq = frame.get("seq")
                with self._loss_lock:
                    if seq in self._loss_pending:
                        self._loss_pending[seq] = True

    # ---------- RTT 测量 ----------

    def _ping_loop(self) -> None:
        """每 1 秒发 ping。用局部变量捕获 socket，避免新旧线程交叉。"""
        sock = self._sock
        while (self._running and not self._stop_event.is_set()
               and sock is self._sock and sock):
            try:
                send_frame(sock, {"type": "ping", "ts": time.perf_counter()})
            except Exception:
                break
            self._stop_event.wait(1.0)

    # ---------- 丢包测量 ----------

    def _loss_loop(self) -> None:
        """每 5 秒发一批 loss_ping，统计丢包率。"""
        sock = self._sock
        while (self._running and not self._stop_event.is_set()
               and sock is self._sock and sock):
            seqs = []
            with self._loss_lock:
                self._loss_pending.clear()
                for i in range(LOSS_BATCH):
                    seq = (int(time.time() * 1000) + i) % 100000
                    self._loss_pending[seq] = False
                    seqs.append(seq)
            try:
                for seq in seqs:
                    if (not self._running or self._stop_event.is_set()
                            or sock is not self._sock):
                        return
                    send_frame(sock, {"type": "loss_ping", "seq": seq,
                                      "ts": time.perf_counter()})
                    self._stop_event.wait(LOSS_SPACING)
            except Exception:
                break

            self._stop_event.wait(LOSS_WAIT)
            if self._stop_event.is_set():
                return
            with self._loss_lock:
                replied = sum(1 for v in self._loss_pending.values() if v)
                total = len(self._loss_pending) or 1
            loss = (total - replied) / total * 100
            self._loss_last = round(loss, 1)
            try:
                self.loss_updated.emit(self._loss_last, self.node_id)
            except RuntimeError:
                pass

            self._stop_event.wait(
                LOSS_INTERVAL - LOSS_BATCH * LOSS_SPACING - LOSS_WAIT)

    def get_loss(self) -> float:
        """最近一次丢包率（%）。"""
        return self._loss_last

    # ---------- 辅助 ----------

    def _emit_status(self, text: str) -> None:
        """状态信号（跨线程安全）。"""
        try:
            self.status_changed.emit(text, self.node_id)
        except RuntimeError:
            pass
