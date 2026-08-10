# -*- coding: utf-8 -*-
"""
副机端 Agent（服务端）包。

v5.0 前后端分离架构：Agent 作为被监控电脑上的后台服务，
① 1 秒采集本机硬件数据（复用 common/collectors/）
② 提供 WebSocket（/ws 实时推送）与 REST API（/api/*）
③ 可选本机仪表盘（本地 Web，本阶段暂不实现）

相关模块：
- config.py            agent_config.json 读写
- aggregator.py        数据聚合器（1 秒组装帧 → 最新帧缓存）
- websocket_server.py  WebSocket 服务端（/ws 多订阅推送 + 鉴权 + PING/PONG）
- http_server.py       REST API（/api/health|nodes|scan|config）
- discovery.py         UDP/mDNS 广播与注册（自动发现）
- main.py              入口（python -m agent）
"""
