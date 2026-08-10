# -*- coding: utf-8 -*-
"""
性能兜底机制（见《README.md》§15）。

v5.0：SelfMonitor 已提升到 common/self_monitor.py，供 Agent 与 Host 本机节点共用。
本文件保留为向后兼容的转发模块（host/local_node、tests 仍可能从 host.self_monitor 导入）。
"""
from common.self_monitor import (SelfMonitor,  # noqa: F401
                                 DEGRADE_CPU, RECOVER_CPU, DEGRADE_STREAK)

__all__ = ["SelfMonitor", "DEGRADE_CPU", "RECOVER_CPU", "DEGRADE_STREAK"]
