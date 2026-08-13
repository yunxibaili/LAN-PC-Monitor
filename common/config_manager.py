# -*- coding: utf-8 -*-
"""
统一配置管理器（ConfigManager）—— 统一管理 agent_config.json 与 host_config.json。

v5.0 配置体系优化（设置中心）：
- 统一入口读写两端配置，供 Settings 设置对话框使用。
- 直接读写 agent_config.json / host_config.json（common 自包含，不依赖 agent/host 配置模块）。
- 提供设置项访问/更新的统一接口。

设计目标：Settings 对话框只依赖本模块，不直接碰两端配置文件细节。
"""
import json
import os

from common.utils import generate_token

# 配置文件路径
AGENT_CFG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "agent_config.json")
HOST_CFG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "host_config.json")


class ConfigManager:
    """统一配置管理器：同时管理 Agent 与 Host 配置。"""

    def __init__(self):
        self.agent_cfg = {}
        self.host_cfg = {}
        self._loaded = False

    # ---------- 通用 JSON 读写（common 自包含，不依赖 agent/host 配置模块） ----------

    @staticmethod
    def _read_json(path: str) -> dict:
        """读取 JSON 配置；文件缺失或损坏时返回空字典。"""
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    @staticmethod
    def _write_json(path: str, cfg: dict) -> None:
        """写入 JSON 配置（UTF-8，缩进 2）。"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)

    # ---------- 加载/保存 ----------

    def load(self) -> "ConfigManager":
        """加载两端配置（惰性，重复调用只加载一次）。"""
        if self._loaded:
            return self
        self.agent_cfg = self._read_json(AGENT_CFG_FILE)
        self.host_cfg = self._read_json(HOST_CFG_FILE)
        self._loaded = True
        return self

    def reload(self) -> None:
        """强制重新加载两端配置。"""
        self._loaded = False
        self.load()

    def save_agent(self) -> None:
        self._write_json(AGENT_CFG_FILE, self.agent_cfg)

    def save_host(self) -> None:
        self._write_json(HOST_CFG_FILE, self.host_cfg)

    def save_all(self) -> None:
        self.save_agent()
        self.save_host()

    # ---------- 通用设置 ----------

    def get_language(self) -> str:
        """当前语言（agent 与 host 一致，取 host）。"""
        return self.host_cfg.get("language", "") or "zh_CN"

    def set_language(self, lang: str) -> None:
        self.host_cfg["language"] = lang
        self.agent_cfg["language"] = lang

    def get_theme(self) -> str:
        return self.host_cfg.get("theme", "dark")

    def set_theme(self, theme: str) -> None:
        self.host_cfg["theme"] = theme

    def get_ui_scale(self) -> float:
        return self.host_cfg.get("ui_scale", 1.0)

    def set_ui_scale(self, scale: float) -> None:
        self.host_cfg["ui_scale"] = float(scale)

    # ---------- 告警设置 ----------

    def get_alert(self, path: str) -> dict | None:
        """按指标路径取红线规则。"""
        alerts = self.host_cfg.get("alerts") or []
        for a in alerts:
            if a.get("path") == path:
                return a
        return None

    def set_alert(self, path: str, red=None, warn=None,
                  red_min=None, warn_min=None, name=None) -> None:
        """新增或更新一条红线规则。"""
        alerts = self.host_cfg.setdefault("alerts", [])
        for a in alerts:
            if a.get("path") == path:
                if red is not None:
                    a["red"] = red
                if warn is not None:
                    a["warn"] = warn
                if red_min is not None:
                    a["red_min"] = red_min
                if warn_min is not None:
                    a["warn_min"] = warn_min
                if name:
                    a["name"] = name
                return
        rule = {"path": path, "name": name or path}
        if red is not None:
            rule["red"] = red
        if warn is not None:
            rule["warn"] = warn
        if red_min is not None:
            rule["red_min"] = red_min
        if warn_min is not None:
            rule["warn_min"] = warn_min
        alerts.append(rule)

    # ---------- 采集设置 ----------

    def get_collector_interval(self) -> float:
        return float(self.agent_cfg.get("collect_interval", 1.0))

    def set_collector_interval(self, interval: float) -> None:
        self.agent_cfg["collect_interval"] = float(interval)

    def get_collector(self, key: str, default=True):
        """读取采集开关（gpu/fps/process/temperature）。"""
        return self.agent_cfg.get("collectors", {}).get(key, default)

    def set_collector(self, key: str, value) -> None:
        self.agent_cfg.setdefault("collectors", {})[key] = value

    # ---------- 节点设置 ----------

    def get_auto_discovery(self) -> bool:
        return bool(self.host_cfg.get("auto_discovery", True))

    def set_auto_discovery(self, enabled: bool) -> None:
        self.host_cfg["auto_discovery"] = bool(enabled)

    def get_auto_connect(self) -> bool:
        return bool(self.host_cfg.get("auto_connect", True))

    def set_auto_connect(self, enabled: bool) -> None:
        self.host_cfg["auto_connect"] = bool(enabled)

    def get_hosts(self) -> list:
        return list(self.host_cfg.get("hosts", []))

    def add_host(self, node_id: str, ip: str, port: int,
                 token: str, alias: str = "") -> None:
        hosts = self.host_cfg.setdefault("hosts", [])
        for h in hosts:
            if h.get("node_id") == node_id:
                h.update({"ip": ip, "port": port, "token": token,
                          "alias": alias or f"{ip}:{port}"})
                return
        hosts.append({"node_id": node_id, "ip": ip, "port": port,
                      "token": token, "alias": alias or f"{ip}:{port}"})

    def remove_host(self, node_id: str) -> None:
        self.host_cfg["hosts"] = [h for h in self.host_cfg.get("hosts", [])
                                  if h.get("node_id") != node_id]

    # ---------- 高级设置 ----------

    def get_log_level(self) -> str:
        return self.agent_cfg.get("log_level", "INFO")

    def set_log_level(self, level: str) -> None:
        self.agent_cfg["log_level"] = level
        self.host_cfg["log_level"] = level

    def get_debug_mode(self) -> bool:
        return bool(self.agent_cfg.get("debug_mode", False))

    def set_debug_mode(self, enabled: bool) -> None:
        self.agent_cfg["debug_mode"] = bool(enabled)

    # ---------- 网络设置（v5.1） ----------

    def get_http_port(self) -> int:
        return int(self.agent_cfg.get("http_port", 12345))

    def set_http_port(self, port: int) -> None:
        self.agent_cfg["http_port"] = int(port)

    def get_udp_port(self) -> int:
        return int(self.agent_cfg.get("udp_port", 12346))

    def set_udp_port(self, port: int) -> None:
        self.agent_cfg["udp_port"] = int(port)

    def get_use_multicast(self) -> bool:
        return bool(self.agent_cfg.get("use_multicast", False))

    def set_use_multicast(self, enabled: bool) -> None:
        self.agent_cfg["use_multicast"] = bool(enabled)

    def get_preferred_iface(self) -> str:
        return self.agent_cfg.get("preferred_iface", "")

    def set_preferred_iface(self, iface: str) -> None:
        self.agent_cfg["preferred_iface"] = iface

    # ---------- 启动设置（v5.1） ----------

    def get_agent_auto_start(self) -> bool:
        return bool(self.agent_cfg.get("auto_start", False))

    def set_agent_auto_start(self, enabled: bool) -> None:
        self.agent_cfg["auto_start"] = bool(enabled)

    def get_host_auto_start(self) -> bool:
        return bool(self.host_cfg.get("auto_start", False))

    def set_host_auto_start(self, enabled: bool) -> None:
        self.host_cfg["auto_start"] = bool(enabled)

    def get_onboarded(self) -> bool:
        """首次初始化向导是否已完成。"""
        return bool(self.host_cfg.get("onboarded", False))

    def set_onboarded(self, done: bool) -> None:
        self.host_cfg["onboarded"] = bool(done)
        self.agent_cfg["onboarded"] = bool(done)

    # ---------- token ----------

    def ensure_agent_token(self) -> str:
        """确保 Agent 有 token，无则生成。"""
        if not self.agent_cfg.get("token"):
            self.agent_cfg["token"] = generate_token()
            self.save_agent()
        return self.agent_cfg["token"]


# 模块级单例（避免多处重复创建）
_default = None


def get_config_manager() -> ConfigManager:
    """获取全局 ConfigManager 单例。"""
    global _default
    if _default is None:
        _default = ConfigManager()
        _default.load()
    return _default


# v5.1 Desktop Experience：SettingsManager 为 ConfigManager 的别名（统一设置管理入口）
SettingsManager = ConfigManager


def get_settings_manager() -> ConfigManager:
    """获取全局 SettingsManager 单例（与 ConfigManager 同一实例）。"""
    return get_config_manager()
