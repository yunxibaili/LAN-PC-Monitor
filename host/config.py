# -*- coding: utf-8 -*-
"""
监控主机配置模块 —— host_config.json 读写（见《README.md》§12.2）。
"""
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "host_config.json")

DEFAULT_CONFIG = {
    "hosts": [],                # [{node_id, ip, port, token, alias}]
    "udp_port": 12346,          # UDP 心跳监听端口
    "window_geometry": {"x": 100, "y": 100, "w": 1400, "h": 900},
    "view_mode": "auto",        # auto/single/multi/overview
    "max_overview_cards": 16,   # 概览最大卡片数
    "max_cards_per_row": 4,     # 每行卡片数
    "last_selected_node": "",   # 上次选中的 node_id
    "alert_popup": True,        # 红线告警弹窗（系统托盘气泡）开关
}

# 内置默认红线（参考行业监控标准，见《README.md》第四篇 §2.3）
DEFAULT_ALERTS = [
    {"path": "cpu.total_usage", "name": "CPU 使用率", "red": 95, "warn": 80},
    {"path": "gpu.usage_percent", "name": "GPU 使用率", "red": 95, "warn": 80},
    {"path": "ram.usage_percent", "name": "内存", "red": 90, "warn": 80},
    {"path": "cpu.package_temp_c", "name": "CPU 温度", "red": 90, "warn": 80},
    {"path": "gpu.core_temp_c", "name": "GPU 温度", "red": 90, "warn": 80},
    {"path": "gpu.hotspot_temp_c", "name": "GPU 热点", "red": 105, "warn": 95},
    {"path": "disk[0].usage_percent", "name": "系统盘", "red": 95, "warn": 85},
    {"path": "net_quality.quality_score", "name": "网络评分",
     "red_min": 50, "warn_min": 60},
]


def load_alerts(cfg: dict) -> list:
    """
    从配置加载红线规则；`alerts` 缺失用内置默认，`"alerts": []` 完全关闭。

    :param cfg: host_config 配置字典
    :return: 规则列表（已过滤非法规则）
    """
    if "alerts" in cfg and cfg["alerts"] is not None:
        raw = cfg["alerts"]
        return [r for r in raw if _validate_alert(r)]
    return list(DEFAULT_ALERTS)


def _validate_alert(rule) -> bool:
    """
    校验单条红线规则：path 非空，且至少含 red/warn 或 red_min/warn_min 之一。
    非法规则日志提示并返回 False。
    """
    import logging
    log = logging.getLogger("host.config")
    if not rule.get("path"):
        log.warning("红线规则缺少 path，已跳过: %s", rule)
        return False
    has_upper = rule.get("red") is not None or rule.get("warn") is not None
    has_lower = rule.get("red_min") is not None or rule.get("warn_min") is not None
    if not has_upper and not has_lower:
        log.warning("红线规则缺少阈值（red/warn/red_min/warn_min），已跳过: %s", rule)
        return False
    return True


def load_config() -> dict:
    """加载主机配置；文件缺失或字段缺失时用默认值补全。"""
    cfg = dict(DEFAULT_CONFIG)
    cfg["window_geometry"] = dict(DEFAULT_CONFIG["window_geometry"])
    # alerts 默认不写入（缺失时 load_alerts 返回内置默认）
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            cfg.update({k: v for k, v in saved.items() if k in cfg})
            if "window_geometry" in saved:
                cfg["window_geometry"].update(saved["window_geometry"])
            if "alerts" in saved:
                cfg["alerts"] = saved["alerts"]
        except (json.JSONDecodeError, OSError) as e:
            print(f"[host_config] 配置解析失败，使用默认配置: {e}")
    return cfg


def save_config(cfg: dict) -> None:
    """将配置写入 host_config.json（UTF-8）。"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def upsert_host(cfg: dict, node_id: str, ip: str, port: int,
                token: str, alias: str) -> dict:
    """添加或更新一个节点；已存在则更新字段。"""
    hosts = cfg.setdefault("hosts", [])
    for h in hosts:
        if h["node_id"] == node_id:
            h.update({"ip": ip, "port": port, "token": token, "alias": alias})
            save_config(cfg)
            return cfg
    hosts.append({
        "node_id": node_id, "ip": ip, "port": port,
        "token": token, "alias": alias or f"{ip}:{port}",
    })
    save_config(cfg)
    return cfg


def remove_host(cfg: dict, node_id: str) -> dict:
    """按 node_id 移除节点。"""
    cfg["hosts"] = [h for h in cfg.get("hosts", []) if h["node_id"] != node_id]
    save_config(cfg)
    return cfg
