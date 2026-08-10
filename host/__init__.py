# -*- coding: utf-8 -*-
"""
监控主机（Host · 集中显示 GUI）包。

v5.0 架构：监控主机作为 WebSocket 客户端同时连接所有 Agent（副机端），集中显示。
本机节点通过本地采集器直供 GUI（不经网络）。
- config.py        host_config.json 读写
- connection.py    NodeConnection（WebSocket 多节点连接+重连+RTT/loss）
- discovery.py     UDP 心跳监听
- local_node.py    本机节点（本地采集器，不经网络）
- self_monitor.py  性能兜底（转发 common.self_monitor）
- gui/             主窗口与界面组件
"""
