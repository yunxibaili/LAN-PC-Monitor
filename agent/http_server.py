# -*- coding: utf-8 -*-
"""
Agent REST API 服务端 —— /api/* 辅助接口（见《README.md》§4.5 / §20）。

基于 aiohttp，与 WebSocket 共用同一端口（单应用）：

- GET  /api/health   健康检查
- GET  /api/nodes    本机信息 + 已配置节点列表
- POST /api/scan     触发自动发现扫描（返回候选 Agent）
- GET  /api/config   读取配置（不含 token）
- POST /api/config   更新配置（别名/日志级别/采集开关，token 不可经此修改）

鉴权：Authorization: Bearer <token> 头，或 ?token=<token> 查询参数（§4.4）。
"""
import json
import logging
import socket
import time

from aiohttp import web

from common.utils import get_lan_ip

log = logging.getLogger("agent.http")

# Agent 进程启动时间（模块加载时记录，用于 agent_uptime）
_AGENT_START_TS = time.time()

# REST 鉴权失败日志限流
_REST_AUTH_FAIL_WINDOW = 60
_REST_AUTH_FAIL_THRESHOLD = 10
_rest_auth_fail_state = {"ts": [], "count": 0}


def _bearer_token(request: web.Request) -> str | None:
    """从 Authorization: Bearer <token> 头取 token。"""
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


class RestServer:
    """REST API 服务端。"""

    def __init__(self, cfg: dict, aggregator=None):
        """
        :param cfg:        Agent 配置字典（agent_config.json）
        :param aggregator: DataAggregator 实例（提供 latest_frame()）
        """
        self.cfg = cfg
        self.aggregator = aggregator
        self._app = None

    # ---------- 鉴权 ----------

    def _check_auth(self, request: web.Request) -> bool:
        """校验 token（Bearer 头或 ?token= 查询参数）。空 token 放行。"""
        token = self.cfg.get("token", "")
        if not token:
            return True
        supplied = _bearer_token(request) or request.query.get("token")
        return supplied == token

    def _require_auth(self, request: web.Request) -> bool:
        """鉴权失败时写 401 并返回 False。失败日志限流，避免刷屏。"""
        if self._check_auth(request):
            return True
        self._log_auth_fail(request.remote)
        raise web.HTTPUnauthorized(text=json.dumps(
            {"error": "unauthorized"}), content_type="application/json")

    def _log_auth_fail(self, ip: str) -> None:
        """REST 鉴权失败限流：普通失败 DEBUG，连续失败合并 WARNING。"""
        now = time.time()
        st = _rest_auth_fail_state
        st["ts"] = [t for t in st["ts"] if now - t < _REST_AUTH_FAIL_WINDOW]
        st["ts"].append(now)
        st["count"] = len(st["ts"])
        if st["count"] >= _REST_AUTH_FAIL_THRESHOLD:
            if st["count"] == _REST_AUTH_FAIL_THRESHOLD:
                log.warning(
                    "REST 鉴权失败 %d 次（%ds 内，来自 %s），疑似探测，后续降级为 DEBUG",
                    st["count"], _REST_AUTH_FAIL_WINDOW, ip)
        else:
            log.debug("REST 鉴权失败: %s（普通失败）", ip)

    # ---------- 路由 ----------

    async def health(self, request: web.Request) -> web.Response:
        """GET /api/health —— 健康检查。"""
        self._require_auth(request)
        frame = self.aggregator.latest_frame() if self.aggregator else {}
        system_uptime = frame.get("system", {}).get("uptime_seconds", 0)
        return web.json_response({
            "status": "ok",
            "version": "5.0.0",
            "hostname": socket.gethostname(),
            "ip": get_lan_ip(self.cfg.get("preferred_iface", "")),
            "port": self.cfg.get("http_port", 12345),
            # v5.0 稳定性优化：区分 Agent 进程 uptime 与系统开机 uptime，禁止混用
            "agent_uptime": int(time.time() - _AGENT_START_TS),
            "system_uptime": system_uptime,
            "subscribers": self.aggregator.connected_clients() if self.aggregator else 0,
        })

    async def nodes(self, request: web.Request) -> web.Response:
        """GET /api/nodes —— 本机信息 + 已配置节点列表。"""
        self._require_auth(request)
        return web.json_response({
            "self": {
                "hostname": socket.gethostname(),
                "ip": get_lan_ip(self.cfg.get("preferred_iface", "")),
                "port": self.cfg.get("http_port", 12345),
                "alias": socket.gethostname(),
            },
            "nodes": [],   # Agent 之间的节点管理（v5.0 副机间不直接通信）
        })

    async def scan(self, request: web.Request) -> web.Response:
        """POST /api/scan —— 触发自动发现扫描（本阶段返回空候选，留接口）。"""
        self._require_auth(request)
        # v5.0 Agent 之间不直接通信；扫描由 Host 侧本地 mDNS/UDP 完成。
        # 此接口保留用于未来"Agent 侧扫描"，当前返回空列表。
        return web.json_response({"found": []})

    async def get_config(self, request: web.Request) -> web.Response:
        """GET /api/config —— 读取配置（不返回 token）。"""
        self._require_auth(request)
        safe = {k: v for k, v in self.cfg.items() if k != "token"}
        return web.json_response(safe)

    async def post_config(self, request: web.Request) -> web.Response:
        """POST /api/config —— 更新配置（别名/日志级别/采集开关）。"""
        self._require_auth(request)
        try:
            data = await request.json()
        except Exception:
            raise web.HTTPBadRequest(text=json.dumps(
                {"error": "invalid json"}), content_type="application/json")
        # 允许更新的白名单字段
        allowed = {"alias", "log_level"}
        for k, v in data.items():
            if k in allowed:
                self.cfg[k] = v
        # token 不可经此接口修改（§20.1 明确）
        return web.json_response({"ok": True})

    # ---------- 应用 ----------

    def make_app(self) -> web.Application:
        """构建 aiohttp 应用并注册 REST 路由。"""
        app = web.Application()
        app.router.add_get("/api/health", self.health)
        app.router.add_get("/api/nodes", self.nodes)
        app.router.add_post("/api/scan", self.scan)
        app.router.add_get("/api/config", self.get_config)
        app.router.add_post("/api/config", self.post_config)
        self._app = app
        return app
