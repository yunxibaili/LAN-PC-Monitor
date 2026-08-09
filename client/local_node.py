# -*- coding: utf-8 -*-
"""
副机端本机节点 —— 复用监控主机的 LocalCollectorPack（见《README.md》§6.2 / §18）。

本机数据由本地采集器直供 GUI，不经网络，与远程节点数据结构统一。
副机端与主机端复用同一 LocalCollectorPack 实现。
"""
from host.local_node import LOCAL_NODE_ID, LocalCollectorPack  # noqa: F401

__all__ = ["LOCAL_NODE_ID", "LocalCollectorPack"]
