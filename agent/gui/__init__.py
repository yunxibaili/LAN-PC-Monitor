# -*- coding: utf-8 -*-
"""
Agent 本机仪表盘 GUI 包（可选，见《README.md》§5.4 方案 A）。

副机端 Agent 默认后台运行（采集 + WS/REST 推送）；
启用 `--gui`（或打包时带 GUI）时，弹出本机仪表盘：
- 本机全部采集数据（本地采集器直供，不经网络）
- 连接信息区（IP/端口/Token/连接串，一键复制）
- 后台服务状态（HTTP/WS 端口、订阅者数）

复用 host/gui/detail_panel.DetailPanel 与 host/local_node.LocalCollectorPack。
"""
