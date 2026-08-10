# -*- coding: utf-8 -*-
"""
采集器工厂（见《README.md》§5.2 / §8）。

v5.0：采集器从 node/collectors 迁移到 common/collectors，
Agent 与 Host 本机节点共用此套采集器（§16：common/collectors/ 复用）。
create_collectors(cfg) 按配置创建全部采集器实例。
"""
import logging

from common.collectors.base import BaseCollector
from common.collectors.cpu_collector import CpuCollector
from common.collectors.ram_collector import RamCollector
from common.collectors.disk_collector import DiskCollector
from common.collectors.net_collector import NetCollector
from common.collectors.proc_collector import ProcCollector
from common.collectors.sys_collector import SysCollector
from common.collectors.gpu_collector import GpuCollector
from common.collectors.net_quality_collector import NetQualityCollector
from common.collectors.fps_collector import FpsCollector

log = logging.getLogger("common.collectors")


def create_collectors(cfg: dict) -> dict:
    """
    按配置创建全部采集器实例。

    :param cfg: 采集节点配置字典（agent_config.json / node_config.json）
    :return: {"cpu":..., "ram":..., "disk":..., "net":..., "processes":...,
              "system":..., "gpu":..., "net_quality":..., "fps":...}
    注意：进程采集器 key 为 "processes"、系统信息采集器 key 为 "system"
    （与 §7 Schema / 聚合器 section 一致）。
    """
    preferred = cfg.get("preferred_iface", "")
    collectors_cfg = cfg.get("collectors", {})
    gpu_index = cfg.get("gpu_index", 0)

    # 帧率模式：collectors.fps = "presentmon"(默认) | "dxgi" | false（§11.8）
    fps_mode = collectors_cfg.get("fps", "presentmon")
    if fps_mode is False:
        fps_mode = "none"

    collectors = {
        "cpu": CpuCollector(),
        "ram": RamCollector(),
        "disk": DiskCollector(),
        "net": NetCollector(preferred_iface=preferred),
        "processes": ProcCollector(),
        "system": SysCollector(preferred_iface=preferred),
        "gpu": GpuCollector(gpu_index=gpu_index),
        "net_quality": NetQualityCollector(),
        "fps": FpsCollector(mode=fps_mode),
    }
    # 采集项开关（§13 增强点 #30）：关闭的采集器不启动
    if collectors_cfg.get("gpu") is False:
        collectors["gpu"]._backend = "none"
    return collectors


def start_all(collectors: dict) -> None:
    """启动所有采集器线程。"""
    for name, col in collectors.items():
        col.start()
        log.info("采集器 %s 已启动", name)


def stop_all(collectors: dict) -> None:
    """停止所有采集器线程。"""
    for name, col in collectors.items():
        col.stop()
    log.info("全部采集器已停止")
