# -*- coding: utf-8 -*-
"""
Agent WebSocket 服务端 —— /ws 多订阅推送 + 鉴权 + PING/PONG（见《README.md》§4）。

基于 aiohttp 内置 WebSocket：
- 连接 ws://<ip>:12345/ws?token=xxx（查询参数鉴权，§4.4 推荐方式）
- 也支持首帧 {"type":"auth","token":xxx}（备选）
- 鉴权通过后加入订阅者集合；推送协程每秒向所有订阅者广播 monitor_data
- RTT：aiohttp 底层对 WS PING 自动回 PONG（RFC 6455），Host 本地测时延
- loss_ping/loss_pong：应用层低频丢包测量（§4.7），收到 loss_ping 回 loss_pong
"""
import asyncio
import json
import logging
import time

from aiohttp import WSMsgType, web

log = logging.getLogger("agent.websocket")

# 默认每 10 秒发 3 个 loss_ping 的回应（Host 侧发起，Agent 侧只需回 pong）
LOSS_INTERVAL = 10.0

# 鉴权失败日志限流（§5.5）：普通失败降级为 DEBUG，
# 同一来源连续失败只记录一次 WARNING，避免刷屏。
_AUTH_FAIL_LOG_WINDOW = 60   # 秒
_AUTH_FAIL_LOG_THRESHOLD = 5 # 窗口内超过 N 次则降级为 INFO，并合并记录


class WebSocketServer:
    """WebSocket 服务端：管理订阅者集合，向所有订阅者广播数据帧。"""

    def __init__(self, token: str = "", aggregator=None):
        """
        :param token:      鉴权 token（空串表示不鉴权，仅测试用）
        :param aggregator: DataAggregator 实例（提供 latest_frame()）
        """
        self.token = token or ""
        self.aggregator = aggregator
        self._subscribers = set()   # 已鉴权 WebSocketResponse 集合
        self._stopping = False
        # 鉴权失败限流状态
        self._auth_fail_lock = asyncio.Lock()
        self._auth_fail_ts = {}     # ip → [timestamps]
        self._auth_fail_count = {}  # ip → 窗口内次数

    # ---------- 计数 ----------

    def subscriber_count(self) -> int:
        """当前 WS 订阅者数。"""
        return len(self._subscribers)

    # ---------- 鉴权失败日志限流 ----------

    async def _log_auth_fail(self, ip: str) -> None:
        """
        记录一次鉴权失败。普通失败打 DEBUG；
        窗口内连续失败超过阈值，合并为一条 WARNING 提示可能存在恶意探测。
        """
        now = time.time()
        async with self._auth_fail_lock:
            # 清理过期窗口
            ts_list = [t for t in self._auth_fail_ts.get(ip, [])
                       if now - t < _AUTH_FAIL_LOG_WINDOW]
            ts_list.append(now)
            self._auth_fail_ts[ip] = ts_list
            count = len(ts_list)
            self._auth_fail_count[ip] = count

        if count >= _AUTH_FAIL_LOG_THRESHOLD:
            # 连续失败（疑似探测）→ 合并 WARNING（每窗口至多刷一次）
            if count == _AUTH_FAIL_LOG_THRESHOLD:
                log.warning(
                    "%s 鉴权失败 %d 次（%ds 内），疑似恶意探测，后续降级为 DEBUG",
                    ip, count, _AUTH_FAIL_LOG_WINDOW)
        else:
            log.debug("WS 鉴权失败: %s（普通失败）", ip)

    # ---------- 路由处理 ----------

    async def ws_handler(self, request: web.Request) -> web.WebSocketResponse:
        """/ws 连接处理：鉴权 → 加入订阅者 → 循环接收消息/心跳。"""
        ws = web.WebSocketResponse(max_msg_size=16 * 1024 * 1024,
                                   heartbeat=30)  # 30s 服务端心跳保活
        await ws.prepare(request)

        # ---- 鉴权 ----
        auth_ok = False
        # 方式一：查询参数 ?token=xxx（推荐，握手阶段校验）
        q_token = request.query.get("token")
        if q_token is not None and self._check_token(q_token):
            auth_ok = True
        # 方式二：首帧 auth（备选）
        if not auth_ok:
            try:
                first = await asyncio.wait_for(ws.receive(), timeout=5)
                if first.type == WSMsgType.TEXT:
                    msg = json.loads(first.data)
                    if msg.get("type") == "auth" and self._check_token(
                            msg.get("token")):
                        auth_ok = True
            except (asyncio.TimeoutError, json.JSONDecodeError, Exception):
                pass

        if not auth_ok:
            await self._log_auth_fail(request.remote)
            try:
                await ws.send_str(json.dumps(
                    {"type": "auth_result", "ok": False, "reason": "token错误"}))
            except Exception:
                pass
            await ws.close(code=1008, message=b"unauthorized")
            return ws

        # P1-1 fix: 先发 auth_result 再入订阅集合，避免竞态
        try:
            await ws.send_str(json.dumps(
                {"type": "auth_result", "ok": True}, ensure_ascii=False))
        except Exception:
            await ws.close(code=1008, message=b"unauthorized")
            return ws

        self._subscribers.add(ws)
        log.info("WS 客户端 %s 已连接，当前订阅者 %d",
                 request.remote, self.subscriber_count())

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self._handle_text(ws, msg.data)
                elif msg.type == WSMsgType.ERROR:
                    break
        except Exception:
            pass
        finally:
            self._subscribers.discard(ws)
            log.info("WS 客户端 %s 断开，当前订阅者 %d",
                     request.remote, self.subscriber_count())
        return ws

    # ---------- 内部实现 ----------

    def _check_token(self, token) -> bool:
        """校验 token（P2-2: 恒时比较 + P2-3: 空 token 禁止放行）。"""
        import hmac
        if not self.token:
            log.warning("Agent token 为空，拒绝所有连接（P2-3）")
            return False
        if not token:
            return False
        return hmac.compare_digest(str(token), self.token)

    async def _handle_text(self, ws, data: str) -> None:
        """处理业务文本消息（loss_ping 等）。"""
        try:
            msg = json.loads(data)
        except json.JSONDecodeError:
            return
        mtype = msg.get("type")
        if mtype == "loss_ping":
            try:
                await ws.send_str(json.dumps({
                    "type": "loss_pong",
                    "seq": msg.get("seq"),
                    "ts": msg.get("ts"),
                }, ensure_ascii=False))
            except Exception:
                pass

    # ---------- 广播 ----------

    async def broadcast_frame(self, frame: dict) -> None:
        """向所有订阅者广播一帧。

        防 HOL 阻塞（P2-6）：每个订阅者单独设 5s 超时，慢/不读的订阅者被剔除，
        避免拖垮整轮广播。序列化失败时仅记录并跳过本帧（不杀死 push_loop）。
        """
        if not self._subscribers:
            return
        try:
            data = json.dumps(frame, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            log.warning("广播帧序列化失败，跳过本帧: %s", e)
            return
        dead = []
        for ws in list(self._subscribers):
            try:
                await asyncio.wait_for(ws.send_str(data), timeout=5.0)
            except (asyncio.TimeoutError, Exception):
                dead.append(ws)
        for ws in dead:
            self._subscribers.discard(ws)

    async def push_loop(self) -> None:
        """每秒从聚合器取最新帧广播（§4.2）。

        P9: 节拍补偿 —— sleep(1.0 - 广播耗时)，避免广播耗时导致节拍漂移。
        """
        while not self._stopping:
            t0 = time.time()
            if self.aggregator is not None:
                frame = self.aggregator.latest_frame()
                if frame:
                    await self.broadcast_frame(frame)
            elapsed = time.time() - t0
            await asyncio.sleep(max(0.0, 1.0 - elapsed))

    def start_push_loop(self) -> None:
        """在事件循环中启动推送协程（main 中调用）。"""
        self._stopping = False
        asyncio.ensure_future(self.push_loop())

    def stop(self) -> None:
        """标记停止推送循环。"""
        self._stopping = True
