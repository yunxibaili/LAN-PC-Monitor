# -*- coding: utf-8 -*-
"""
监控主机配置模块 —— host_config.json 读写（见《技术文档.md》§12.2）。
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
}


def load_config() -> dict:
    """加载主机配置；文件缺失或字段缺失时用默认值补全。"""
    cfg = dict(DEFAULT_CONFIG)
    cfg["window_geometry"] = dict(DEFAULT_CONFIG["window_geometry"])
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            cfg.update({k: v for k, v in saved.items() if k in cfg})
            if "window_geometry" in saved:
                cfg["window_geometry"].update(saved["window_geometry"])
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
