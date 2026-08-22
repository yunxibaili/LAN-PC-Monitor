# -*- coding: utf-8 -*-
"""
网络质量采集器（见《README.md》§8.6 / §18.5）。

节点端仅采集"到网关延迟"（系统 ping 解析，中英文兼容，免提权）。
- latency_to_client_ms：按 §18.5 方案 A 填 null（RTT 由监控主机本地测量）。
- 评分/等级：节点端 N/A（主机端以自己测量为准）。
"""
import logging

from common.utils import get_default_gateway, ping_gateway
from common.collectors.base import BaseCollector

log = logging.getLogger("common.collectors.net_quality")


class NetQualityCollector(BaseCollector):
    """网络质量采集器：5 秒间隔（网关 ping 较重，延迟变化慢）。"""

    def __init__(self, interval: float = 5.0):
        super().__init__(interval)

    def collect(self) -> dict:
        """采集网关延迟。"""
        gateway = get_default_gateway()
        latency = None
        if gateway:
            latency = ping_gateway(gateway)
        return {
            "latency_to_client_ms": None,   # §18.5 方案 A：主机本地测量
            "latency_to_gateway_ms": round(latency, 1) if latency is not None else "N/A",
            "packet_loss_percent": "N/A",   # 丢包率由主机 loss_ping 测量
            "quality_score": "N/A",
            "quality_grade": "N/A",
        }
