# -*- coding: utf-8 -*-
"""
v5.2 Host Service 层 —— 业务编排服务。

- AlertService：FrameStore → AlertEngine → AlertAdapter → AlertStore。
- DiscoveryService：节点发现服务（UDP + mDNS 统一）。
"""
from host.service.alert_service import AlertService        # noqa: F401
from host.service.discovery_service import DiscoveryService  # noqa: F401

__all__ = ["AlertService", "DiscoveryService"]
