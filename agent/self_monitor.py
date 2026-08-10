# -*- coding: utf-8 -*-
"""
Agent 性能兜底 —— 检测本程序 CPU 占用，超限自动降级（见《README.md》§15）。

SelfMonitor 已在 common/self_monitor.py（v5.0 提升），Agent 直接复用。
为遵循双端分离，Agent 不从 host 包导入。
"""
from common.self_monitor import (SelfMonitor,  # noqa: F401
                                 DEGRADE_CPU, RECOVER_CPU, DEGRADE_STREAK)

__all__ = ["SelfMonitor", "DEGRADE_CPU", "RECOVER_CPU", "DEGRADE_STREAK"]
