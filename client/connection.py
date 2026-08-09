# -*- coding: utf-8 -*-
"""
副机端节点连接器 —— 复用监控主机的 NodeConnection（见《README.md》§6.6 / §18）。

副机端与主机端使用相同的 NodeConnection 逻辑（连接/鉴权/重连/RTT/丢包），
直接从 host.connection 复用，避免重复代码。所有信号带 node_id。
"""
from host.connection import NodeConnection  # noqa: F401  复用主机端连接器

__all__ = ["NodeConnection"]
