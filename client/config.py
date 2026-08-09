# -*- coding: utf-8 -*-
"""
副机端配置模块 —— client_config.json 读写（见《README.md》§13.2）。

副机端仅保存节点列表摘要（IP/端口/别名/token/状态），不存储详细历史数据。
"""
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "client_config.json")

DEFAULT_CONFIG = {
    "nodes": [],                # [{node_id, ip, port, token, alias}]
    "udp_port": 12346,          # UDP 心跳监听端口
    "window_geometry": {"x": 100, "y": 100, "w": 1000, "h": 700},
    "log_level": "INFO",        # 日志级别（§12.2）
    "gui_refresh_interval": 1.0,  # GUI 刷新间隔秒（§20.10，预留）
    "last_selected_node": "localhost",
}


def load_config() -> dict:
    """加载副机端配置；文件缺失或字段缺失时用默认值补全。"""
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
            print(f"[client_config] 配置解析失败，使用默认配置: {e}")
    return cfg


def save_config(cfg: dict) -> None:
    """将配置写入 client_config.json（UTF-8）。"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def upsert_node(cfg: dict, node_id: str, ip: str, port: int,
                token: str, alias: str) -> dict:
    """添加或更新一个节点；已存在则更新字段。"""
    nodes = cfg.setdefault("nodes", [])
    for n in nodes:
        if n["node_id"] == node_id:
            n.update({"ip": ip, "port": port, "token": token, "alias": alias})
            save_config(cfg)
            return cfg
    nodes.append({
        "node_id": node_id, "ip": ip, "port": port,
        "token": token, "alias": alias or f"{ip}:{port}",
    })
    save_config(cfg)
    return cfg


def remove_node(cfg: dict, node_id: str) -> dict:
    """按 node_id 移除节点。"""
    cfg["nodes"] = [n for n in cfg.get("nodes", []) if n["node_id"] != node_id]
    save_config(cfg)
    return cfg
