# -*- coding: utf-8 -*-
"""
Host 网络层核心 —— 纯 Python WebSocket 客户端（无 PyQt5 依赖）。

v5.0 稳定性优化：
- 从 host/connection.py 拆出，去除 PyQt5 强依赖，无 GUI 环境也可测试。
- 显式连接状态机：connecting → authenticating → connected / failed。
- 错误 token 明确表现为 failed（authenticating → failed），不表现为已连接。

信号机制：本模块不依赖 Qt。上层（PyQt5 NodeConnection）通过回调订阅事件。
"""
import json
import logging
import threading
import time

import websocket  # websocket-client

log = logging.getLogger("host.connection_core")

# 丢包测量参数（§4.7：低频补充测量，每 10 秒 3 个）
LOSS_INTERVAL = 10.0
LOSS_BATCH = 3
LOSS_SPACING = 0.1
LOSS_WAIT = 1.0

# WS 连接超时（秒）
WS_CONNECT_TIMEOUT = 5
WS_READ_TIMEOUT = 30

# 连接状态（内部状态码）
STATE_CONNECTING = "connecting"          # 正在建立 TCP/WS 连接
STATE_AUTHENTICATING = "authenticating"  # 已连接，等待/校验鉴权结果
STATE_CONNECTED = "connected"            # 鉴权通过，数据推送中
STATE_AUTH_FAILED = "auth_failed"        # 鉴权失败（token 错误）
STATE_OFFLINE = "offline"                # 连接失败/网络错误
STATE_TIMEOUT = "timeout"                # 连接超时
STATE_RECONNECTING = "reconnecting"      # 断开后重连等待中


class ConnectionCore:
    """
    单 Agent 的 WebSocket 连接核心（纯 Python）。

    通过回调（callbacks）向上层报告事件，回调签名：
        on_state(state: str, node_id: str)
        on_data(frame: dict, node_id: str)
        on_rtt(rtt_ms: float, node_id: str)
        on_loss(loss: float, node_id: str)
    """

    def __init__(self, node_id: str, ip: str, port: int, token: str,
                 alias: str = "", callbacks: dict | None = None):
        self.node_id = node_id
        self.ip = ip
        self.port = port
        self.token = token or ""
        self.alias = alias or f"{ip}:{port}"
        self.callbacks = callbacks or {}
        self._ws = None
        self._running = True
        self._stop_event = threading.Event()
        self._state = None          # 初始 None，首次 _set_state 即触发回调
        # 丢包统计状态
        self._loss_lock = threading.Lock()
        self._loss_pending = {}
        self._loss_last = 0.0
        # RTT 状态
        self._last_rtt = 0.0
        # 日志带 node_id 标签（§11.2）
        self.log = logging.getLogger(f"host.node.{node_id}")

    # ---------- 对外接口 ----------

    def start(self) -> None:
        """启动连接线程（daemon）。"""
        threading.Thread(target=self._connect_loop, daemon=True,
                         name=f"node-conn-{self.node_id}").start()

    def stop(self) -> None:
        """停止连接并关闭 WebSocket。"""
        self._stop_event.set()
        self._running = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass

    @property
    def state(self) -> str:
        """当前连接状态。"""
        return self._state

    def is_connected(self) -> bool:
        """是否已鉴权通过并处于数据推送中。"""
        return self._state == STATE_CONNECTED

    def get_loss(self) -> float:
        return self._loss_last

    def get_rtt(self) -> float:
        return self._last_rtt

    # ---------- 状态机 ----------

    def _set_state(self, state: str) -> None:
        """更新状态并触发回调（跨线程安全）。"""
        if self._state != state:
            self._state = state
            cb = self.callbacks.get("on_state")
            if cb:
                try:
                    cb(state, self.node_id)
                except Exception:
                    pass

    def _emit_data(self, frame: dict) -> None:
        cb = self.callbacks.get("on_data")
        if cb:
            try:
                cb(frame, self.node_id)
            except Exception:
                pass

    def _emit_rtt(self, rtt_ms: float) -> None:
        cb = self.callbacks.get("on_rtt")
        if cb:
            try:
                cb(rtt_ms, self.node_id)
            except Exception:
                pass

    def _emit_loss(self, loss: float) -> None:
        cb = self.callbacks.get("on_loss")
        if cb:
            try:
                cb(loss, self.node_id)
            except Exception:
                pass

    # ---------- 连接主循环 ----------

    def _build_ws_url(self) -> str:
        return f"ws://{self.ip}:{self.port}/ws?token={self.token}"

    def _connect_loop(self) -> None:
        """连接 + 鉴权 + 指数退避重连循环（状态机驱动）。

        鉴权失败（auth_failed）后**停止重连**：token 错误时无限重连只会反复失败，
        保持 auth_failed 状态等待用户处理（与 v4.0 设计一致）。
        """
        backoff = 1
        while self._running and not self._stop_event.is_set():
            # 1) connecting：建立连接
            self._set_state(STATE_CONNECTING)
            try:
                self._ws = websocket.create_connection(
                    self._build_ws_url(),
                    timeout=WS_CONNECT_TIMEOUT,
                    enable_multithread=True)
            except websocket.WebSocketTimeoutException:
                if self._stop_event.is_set():
                    break
                self._set_state(STATE_TIMEOUT)
                self.log.warning("%s 连接超时", self.alias)
            except Exception as e:
                if self._stop_event.is_set():
                    break
                self._set_state(STATE_OFFLINE)
                self.log.warning("%s 连接失败: %s", self.alias, e)
            else:
                # 2) authenticating：读取鉴权结果
                self._set_state(STATE_AUTHENTICATING)
                first = self._recv_json()
                if first and first.get("ok"):
                    # 3) connected：鉴权通过
                    self._set_state(STATE_CONNECTED)
                    backoff = 1
                    self.log.info("%s 已连接", self.alias)
                    self._start_aux_threads()
                    self._recv_loop()  # 阻塞直到断开
                    self._set_state(STATE_RECONNECTING)
                    if self._stop_event.is_set():
                        break
                    self.log.info("%s 断开", self.alias)
                else:
                    # 鉴权失败：明确 failed，不表现为已连接；停止重连
                    reason = (first or {}).get("reason", "unknown error")
                    self._set_state(STATE_AUTH_FAILED)
                    self.log.info("%s 鉴权失败: %s（token 错误或已过期，停止重连）",
                                  self.alias, reason)
                    self._close_ws()
                    break  # auth_failed 后停止重连，等用户处理
            finally:
                self._close_ws()

            if not self._running or self._stop_event.is_set():
                break
            self._stop_event.wait(backoff)
            backoff = min(backoff * 2, 60)

    def _start_aux_threads(self) -> None:
        """启动 ping/loss 辅助线程。"""
        threading.Thread(target=self._ping_loop, daemon=True,
                         name=f"node-ping-{self.node_id}").start()
        threading.Thread(target=self._loss_loop, daemon=True,
                         name=f"node-loss-{self.node_id}").start()

    # ---------- 接收循环 ----------

    def _recv_loop(self) -> None:
        """阻塞接收 WS 消息，分发给对应回调。"""
        ws = self._ws
        while (self._running and not self._stop_event.is_set()
               and ws is self._ws and ws):
            frame = self._recv_json()
            if frame is None:
                break
            t = frame.get("type")
            if t == "monitor_data":
                self._emit_data(frame)
            elif t == "loss_pong":
                seq = frame.get("seq")
                ts = frame.get("ts")
                with self._loss_lock:
                    if seq in self._loss_pending:
                        self._loss_pending[seq] = True
                if ts is not None:
                    rtt = (time.perf_counter() - ts) * 1000
                    self._last_rtt = rtt
                    self._emit_rtt(round(rtt, 3))

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

    # ---------- RTT / 丢包 ----------

    def _ping_loop(self) -> None:
        """每 1 秒发 WS PING 帧（维持连接活跃）。"""
        ws = self._ws
        while (self._running and not self._stop_event.is_set()
               and ws is self._ws and ws):
            try:
                ws.ping()
            except Exception:
                break
            self._stop_event.wait(1.0)

    def _loss_loop(self) -> None:
        """每 10 秒发一批 loss_ping，统计丢包率并算 RTT。"""
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
            self._emit_loss(self._loss_last)

            self._stop_event.wait(
                LOSS_INTERVAL - LOSS_BATCH * LOSS_SPACING - LOSS_WAIT)

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
