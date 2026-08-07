# -*- coding: utf-8 -*-
"""
采集节点（Node · 无界面后台）包。

v3.0 架构：采集节点作为 TCP Server，纯后台采集 + 推送，
无任何 GUI。相关模块：
- config.py       node_config.json 读写
- tcp_server.py   TCP Server（多监控主机 + 鉴权 + 去重计数）
- discovery.py    UDP 心跳广播（node_heartbeat）
- aggregator.py   数据聚合器（1 秒单路 broadcast）
- fake_data.py    假数据（开发/测试用）
- collectors/     采集器（与监控主机本机节点共用）
"""
