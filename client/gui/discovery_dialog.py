# -*- coding: utf-8 -*-
"""
副机端自动发现弹窗 —— 复用主机端 DiscoveryDialog（见《技术文档.md》§6.4 / §20.9）。

弹窗逻辑完全通用（listener + existing + on_add 回调），直接从 host.gui 复用。
"""
from host.gui.discovery_dialog import DiscoveryDialog  # noqa: F401

__all__ = ["DiscoveryDialog"]
