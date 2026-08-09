# -*- coding: utf-8 -*-
"""
副机端节点发现 —— 复用 node/discovery 的 DiscoveryListener 与 MdnsDiscovery（见《README.md》§4.6 / §23.1）。

- UDP 广播心跳监听（兼容层，跨子网/老旧网络）
- mDNS 零配置发现（同子网，zeroconf，自动降级）
两者并行运行，互为备份，按 ip:port 去重。
"""
from node.discovery import DiscoveryListener, MdnsDiscovery  # noqa: F401

__all__ = ["DiscoveryListener", "MdnsDiscovery"]
