# -*- coding: utf-8 -*-
"""
监控主机单节点连接器 —— NodeConnection（见《README.md》§6.2 / §4.7）。

v5.0：网络层从 TCP 自定义帧升级为 WebSocket（ws://<ip>:port/ws?token=xxx）。
- 连接 → 鉴权（查询参数 token，Agent 端握手阶段校验）→ 接收 monitor_data 帧。
- 断线独立指数退避重连（1s→60s）。
- RTT 测量：WebSocket PING 帧由 Agent 底层自动回 PONG，主机 perf_counter 计算。
- 丢包测量（§4.7）：每 10 秒发 3 个应用层 loss_ping，Agent 回 loss_pong。
- 所有信号带 node_id，GUI 按 node_id 路由。

**接口兼容**：类名 `NodeConnection`、信号 `data_received/status_changed/rtt_updated/loss_updated`
与 v4.0 TCP 版完全一致，GUI（host/gui、client/gui）无需改动装配。
"""
import json
import logging
import threading
import time

from PyQt5.QtCore import QObject, pyqtSignal

# WebSocket 客户端库（v5.0 新增依赖，见《README.md》§16.1）
import websocket  # websocket-client

log = logging.getLogger("host.connection")

# 丢包测量参数（§4.7：低频补充测量，每 10 秒 3 个）
LOSS_INTERVAL = 10.0
LOSS_BATCH = 3
LOSS_SPACING = 0.1
LOSS_WAIT = 1.0

# WS 连接超时（秒）
WS_CONNECT_TIMEOUT = 5
WS_READ_TIMEOUT = 30


class NodeConnection(QObject):
    """
    单个 Agent 的连接对象（WebSocket）。

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
        self._ws = None
        self._running = True
        self._stop_event = threading.Event()
        self._connected = False
        # 丢包统计状态
        self._loss_lock = threading.Lock()
        self._loss_pending = {}
        self._loss_last = 0.0
        # RTT 状态：最近一次 ping 时间戳（由 loss_pong 回显计算）
        self._rtt_lock = threading.Lock()
        self._last_sent_ts = 0.0
        self._last_rtt = 0.0
        # 日志带 node_id 标签（§11.2）
        self.log = logging.getLogger(f"host.node.{node_id}")

    # ---------- 生命周期 ----------

    def start(self) -> None:
        """启动连接线程（daemon）。"""
        threading.Thread(target=self._connect_loop, daemon=True,
                         name=f"node-conn-{self.node_id}").start()

    def stop(self) -> None:
        """停止连接并关闭 WebSocket（stop 驱动断开静默）。"""
        self._stop_event.set()
        self._running = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass

    def is_connected(self) -> bool:
        return self._connected

    # ---------- 连接主循环 ----------

    def _build_ws_url(self) -> str:
        """构造 WebSocket URL（查询参数鉴权，§4.4 推荐方式）。"""
        return f"ws://{self.ip}:{self.port}/ws?token={self.token}"

    def _connect_loop(self) -> None:
        """连接 + 指数退避重连循环。"""
        backoff = 1
        while self._running and not self._stop_event.is_set():
            try:
                # 鉴权在握手阶段完成（URL 查询参数）
                self._ws = websocket.create_connection(
                    self._build_ws_url(),
                    timeout=WS_CONNECT_TIMEOUT,
                    enable_multithread=True)
                # 读取首帧 auth_result（Agent 发送）
                first = self._recv_json()
                if not first or not first.get("ok"):
                    reason = (first or {}).get("reason", "unknown error")
                    self._emit_status("auth_failed")
                    self.log.warning("%s 鉴权失败: %s", self.alias, reason)
                    self._close_ws()
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

            except websocket.WebSocketTimeoutException:
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
                self._close_ws()

            if not self._running or self._stop_event.is_set():
                break
            self._stop_event.wait(backoff)
            backoff = min(backoff * 2, 60)

    # ---------- 接收循环 ----------

    def _recv_loop(self) -> None:
        """阻塞接收 WS 消息，分发给对应信号。"""
        ws = self._ws
        while (self._running and not self._stop_event.is_set()
               and ws is self._ws and ws):
            frame = self._recv_json()
            if frame is None:
                break
            t = frame.get("type")
            if t == "monitor_data":
                self.data_received.emit(frame, self.node_id)
            elif t == "loss_pong":
                seq = frame.get("seq")
                ts = frame.get("ts")
                with self._loss_lock:
                    if seq in self._loss_pending:
                        self._loss_pending[seq] = True
                # 用 loss_pong 回显的时间戳精确计算 RTT（§4.2）
                if ts is not None:
                    rtt = (time.perf_counter() - ts) * 1000
                    self._last_rtt = rtt
                    try:
                        self.rtt_updated.emit(round(rtt, 3), self.node_id)
                    except RuntimeError:
                        pass

    def _recv_json(self) -> dict | None:
        """接收一条 WS 文本消息并解析 JSON；失败/关闭返回 None。"""
        ws = self._ws
        if ws is None:
            return None
        try:
            ws.settimeout(WS_READ_TIMEOUT)
            data = ws.recv()
            if not data:
                return None
            return json.loads(data)
        except Exception:
            return None

    # ---------- RTT 测量（WS PING/PONG） ----------

    def _ping_loop(self) -> None:
        """
        每 1 秒发 WS PING 帧，Agent 底层自动回 PONG（维持连接活跃）。

        精确 RTT 由 loss_pong 回显时间戳计算（见 _recv_loop / _loss_loop）。
        websocket-client 的底层 PING/PONG 不暴露应用层时间戳，
        故 RTT 以 loss_ping/loss_pong（携带 perf_counter）为准，精度 < 1ms。
        """
        ws = self._ws
        while (self._running and not self._stop_event.is_set()
               and ws is self._ws and ws):
            try:
                ws.ping()  # 标准 WS PING 控制帧（Agent 自动回 PONG）
            except Exception:
                break
            self._stop_event.wait(1.0)

    # ---------- 丢包测量 / RTT 精确测量 ----------

    def _loss_loop(self) -> None:
        """每 10 秒发一批 loss_ping（带 perf_counter），统计丢包率并算 RTT。"""
        ws = self._ws
        while (self._running and not self._stop_event.is_set()
               and ws is self._ws and ws):
            seqs = []
            with self._loss_lock:
                self._loss_pending.clear()
                base = int(time.time() * 1000)
                for i in range(LOSS_BATCH):
                    seq = (base + i) % 100000
                    self._loss_pending[seq] = False
                    seqs.append(seq)
            try:
                for seq in seqs:
                    if (not self._running or self._stop_event.is_set()
                            or ws is not self._ws):
                        return
                    ts = time.perf_counter()
                    ws.send(json.dumps({
                        "type": "loss_ping", "seq": seq, "ts": ts},
                        ensure_ascii=False))
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

    def get_rtt(self) -> float:
        """最近一次 RTT（ms）。"""
        return self._last_rtt

    # ---------- 辅助 ----------

    def _close_ws(self) -> None:
        """关闭当前 WebSocket（线程安全）。"""
        ws = self._ws
        self._ws = None
        if ws:
            try:
                ws.close()
            except Exception:
                pass

    def _emit_status(self, text: str) -> None:
        """状态信号（跨线程安全）。"""
        try:
            self.status_changed.emit(text, self.node_id)
        except RuntimeError:
            pass
