# -*- coding: utf-8 -*-
"""
v5.2 Host Manager 层 —— 独立管理模块。

- TrayManager：系统托盘管理（降级安全）。
  （节点发现服务已移至 host/service/discovery_service.py）
"""
from host.manager.tray_manager import TrayManager  # noqa: F401

__all__ = ["TrayManager"]
