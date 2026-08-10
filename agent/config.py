# -*- coding: utf-8 -*-
"""
Agent 配置模块 —— agent_config.json 读写（见《README.md》§12.2）。

由 v4.0 node_config.json 迁移：
- tcp_port → http_port（HTTP + WebSocket 共用端口）
- 保留 udp_port（自动发现）、token、use_multicast、preferred_iface、gpu_index、collectors
"""
import json
import os

from common.utils import generate_token

CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "agent_config.json")

DEFAULT_CONFIG = {
    "http_port": 12345,       # HTTP + WebSocket 共用端口（v5.0，替代 TCP 12345）
    "udp_port": 12346,        # UDP 自动发现端口
    "token": "",              # 空串 → 首次启动自动生成随机 token
    "use_multicast": False,   # False 用广播，True 用组播 239.0.0.1
    "preferred_iface": "",    # 指定网卡名，空则自动选取
    "gpu_index": 0,           # 多 GPU 时指定主卡 index（§8.3.1）
    "collectors": {           # 采集项开关（§10.8）
        "fps": "presentmon",  # "presentmon"(默认) | "dxgi" | false
        "gpu": True,
        "temperature": True,
    },
    "log_level": "INFO",      # 日志级别：DEBUG/INFO/WARNING/ERROR（§11.2）
}


def load_config() -> dict:
    """加载 Agent 配置；文件缺失或字段缺失时用默认值补全。"""
    cfg = dict(DEFAULT_CONFIG)
    cfg["collectors"] = dict(DEFAULT_CONFIG["collectors"])

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            cfg.update({k: v for k, v in saved.items() if k in cfg})
            if "collectors" in saved:
                cfg["collectors"].update(saved["collectors"])
        except (json.JSONDecodeError, OSError) as e:
            print(f"[agent_config] 配置解析失败，使用默认配置: {e}")

    if not cfg.get("token"):
        cfg["token"] = generate_token()
        save_config(cfg)
    return cfg


def save_config(cfg: dict) -> None:
    """将配置写入 agent_config.json（UTF-8）。"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
