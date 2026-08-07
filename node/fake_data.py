# -*- coding: utf-8 -*-
"""
假数据生成器 —— 开发/测试用（见《技术文档.md》§16 node/fake_data.py）。

字段结构对齐 §7 JSON Schema，供无真实硬件环境的链路测试。
"""
import socket
import time

from common.utils import get_lan_ip


class FakeDataGenerator:
    """生成随时间小幅波动的假监控数据，模拟 1 秒刷新。"""

    def __init__(self, seed: int = 0):
        # 用线性同余模拟抖动，无需 random 以便观察趋势
        self._x = (seed * 9301 + 49297) % 233280

    def _rand(self) -> float:
        """0~1 伪随机。"""
        self._x = (self._x * 9301 + 49297) % 233280
        return self._x / 233280

    def make_frame(self, connected_clients: int) -> dict:
        """
        组装一帧完整的 monitor_data 假数据。

        :param connected_clients: 当前唯一监控主机数（由 server 提供）
        """
        cpu_usage = round(40 + self._rand() * 40, 1)
        return {
            "type": "monitor_data",
            "ts": time.time(),
            "hostname": socket.gethostname(),
            "connected_clients": connected_clients,
            "system": {
                "uptime_seconds": 3600 * 12 + int(self._rand() * 3600),
                "local_ip": get_lan_ip(),
            },
            "cpu": {
                "name": "Intel Core i7-10700K (P0 假数据)",
                "total_usage": cpu_usage,
                "per_core_usage": [round(cpu_usage * (0.6 + 0.4 * self._rand()), 1)
                                   for _ in range(8)],
                "physical_cores": 8,
                "logical_cores": 16,
                "core_freq_mhz": 3900 + int(self._rand() * 600),
                "package_temp_c": round(50 + self._rand() * 30, 1),
                "power_w": "N/A",
                "l1_hit_rate": "N/A",
                "l2_hit_rate": "N/A",
                "l3_hit_rate": "N/A",
            },
            "ram": {
                "total_gb": 32.0,
                "used_gb": round(10 + self._rand() * 8, 2),
                "available_gb": round(14 + self._rand() * 8, 2),
                "usage_percent": round(40 + self._rand() * 20, 1),
                "swap_used_mb": round(256 + self._rand() * 512, 1),
            },
            "gpu": {
                "name": "NVIDIA GeForce RTX 3070 (P0 假数据)",
                "usage_percent": round(30 + self._rand() * 60, 1),
                "vram_used_mb": int(2048 + self._rand() * 2048),
                "vram_total_mb": 8192,
                "vram_usage_percent": round(25 + self._rand() * 25, 1),
                "core_temp_c": round(45 + self._rand() * 35, 1),
                "mem_temp_c": "N/A",
                "hotspot_temp_c": round(50 + self._rand() * 40, 1),
                "core_freq_mhz": int(1500 + self._rand() * 400),
                "mem_freq_mhz": int(6800 + self._rand() * 400),
                "power_w": round(60 + self._rand() * 120, 1),
                "power_limit_w": 250.0,
                "engine_usage": {
                    "graphics": round(30 + self._rand() * 60, 1),
                    "compute": round(self._rand() * 10, 1),
                    "encode": round(self._rand() * 5, 1),
                    "decode": round(self._rand() * 5, 1),
                },
                "top_vram_processes": [
                    {"name": "game.exe", "vram_mb": int(1024 + self._rand() * 1024)},
                    {"name": "chrome.exe", "vram_mb": int(256 + self._rand() * 256)},
                    {"name": "discord.exe", "vram_mb": int(128 + self._rand() * 128)},
                ],
            },
            "disk": [
                {
                    "drive": "C:",
                    "read_mb_s": round(self._rand() * 80, 1),
                    "write_mb_s": round(self._rand() * 40, 1),
                    "read_iops": int(self._rand() * 800),
                    "write_iops": int(self._rand() * 400),
                    "queue_depth": round(self._rand() * 2, 2),
                    "temp_c": "N/A",
                    "free_gb": round(150 + self._rand() * 100, 1),
                    "total_gb": 500.0,
                    "usage_percent": round(50 + self._rand() * 30, 1),
                },
                {
                    "drive": "D:",
                    "read_mb_s": round(self._rand() * 50, 1),
                    "write_mb_s": round(self._rand() * 20, 1),
                    "read_iops": int(self._rand() * 400),
                    "write_iops": int(self._rand() * 200),
                    "queue_depth": round(self._rand() * 2, 2),
                    "temp_c": "N/A",
                    "free_gb": round(500 + self._rand() * 300, 1),
                    "total_gb": 1000.0,
                    "usage_percent": round(20 + self._rand() * 30, 1),
                },
            ],
            "net": {
                "interface": "以太网",
                "upload_mb_s": round(self._rand() * 2, 2),
                "download_mb_s": round(self._rand() * 6, 2),
                "link_speed_mbps": 1000,
                "errors_sent": 0,
                "errors_recv": 0,
                "drops_sent": 0,
                "drops_recv": 0,
            },
            "net_quality": {
                "latency_to_client_ms": None,   # §18.5 方案 A：RTT 由监控主机测量
                "latency_to_gateway_ms": round(1 + self._rand() * 4, 1),
                "packet_loss_percent": round(self._rand(), 2),
                "quality_score": 95,
                "quality_grade": "优秀",
            },
            "fps": {
                "window_title": "（P0 假数据，P4 接入 PresentMon）",
                "fps": int(60 + self._rand() * 100),
                "frame_time_ms": round(7 + self._rand() * 5, 2),
                "low_1_percent": int(60 + self._rand() * 80),
                "source": "fake",
            },
            "processes": {
                "top_cpu": [
                    {"name": "chrome.exe", "usage_percent": round(8 + self._rand() * 6, 1)},
                    {"name": "Code.exe", "usage_percent": round(4 + self._rand() * 5, 1)},
                    {"name": "game.exe", "usage_percent": round(2 + self._rand() * 8, 1)},
                ],
                "top_gpu": [
                    {"name": "game.exe", "usage_percent": round(30 + self._rand() * 30, 1)},
                    {"name": "chrome.exe", "usage_percent": round(2 + self._rand() * 4, 1)},
                    {"name": "discord.exe", "usage_percent": round(1 + self._rand() * 2, 1)},
                ],
            },
        }
