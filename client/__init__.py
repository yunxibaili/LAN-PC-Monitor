# -*- coding: utf-8 -*-
"""
副机端（Client · 本机仪表盘 + 节点管理）包。

v4.0 三角色架构：副机端与被监控电脑同机部署。
- 本机仪表盘：显示本机全部数据（本地采集器直供，不经网络）
- 节点管理器：维护已接入节点摘要列表（IP/别名/状态/RTT/评分），
  不显示远程节点详细数据（详情由监控主机集中展示）
- config.py        client_config.json 读写
- connection.py    NodeConnection（多节点连接+重连+ping）
- local_node.py    本机节点（本地采集器，不经网络）
- discovery.py     UDP 心跳监听（自动发现）
- gui/             本机仪表盘 + 节点管理器界面
"""
