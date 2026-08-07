# -*- coding: utf-8 -*-
"""
副机端 UDP 心跳监听 —— 复用 node/discovery 的 DiscoveryListener（见《技术文档.md》§4.6）。

副机端与主机端使用相同的 UDP 心跳监听逻辑，直接从 node.discovery 复用。
"""
from node.discovery import DiscoveryListener  # noqa: F401  复用节点心跳监听

__all__ = ["DiscoveryListener"]
