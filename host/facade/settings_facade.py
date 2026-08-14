# -*- coding: utf-8 -*-
"""
SettingsFacade —— 配置统一入口（v5.2 Phase 0）。

注意：**不新建 settings_manager.py**。本 Facade 直接包装现有
`common.config_manager.ConfigManager`（其 `SettingsManager` 别名指向同一类），
提供页面友好、带默认值兜底的 get/set 接口。

设计（评审建议1）：
    SettingsFacade
        |
        |
    ConfigManager / SettingsManager alias   （同一实例，单例）

职责：
- get/set/reset 统一入口，页面不直接碰配置字典。
- 默认值兜底：新字段（theme/ui_scale/chart_refresh_ms 等）缺失时返回默认。
- 变更通知信号 settings_changed(key)，页面响应式更新。
- 持久化委托给 ConfigManager（agent_config.json + host_config.json）。

本模块依赖 PyQt5 信号（若有），无 PyQt5 时回退为普通类（仍可用，仅无信号）。
"""
import logging

from common.config_manager import get_config_manager
from host.store.signals import Signal

log = logging.getLogger("host.facade.settings")


# v5.2 新增配置字段的默认值（评审 §5；缺失时兜底）
V52_DEFAULTS = {
    "theme": "dark",
    "ui_scale": 1.0,
    "chart_refresh_ms": 500,
    "history_minutes": 5,
    "alert_dedup_seconds": 30,
    "ws_read_timeout": 30,
    "reconnect_interval": 60,
    "language": "zh_CN",
}


class SettingsFacade:
    """配置统一入口，包装现有 ConfigManager（SettingsManager 别名）。"""

    settings_changed = Signal(str)

    def __init__(self, manager=None):
        """
        :param manager: 可注入的 ConfigManager；默认用全局单例。
        """
        self._mgr = manager or get_config_manager()

    # ---------- 通用读 ----------

    def get(self, key: str, default=None):
        """按 key 读取配置（先查 ConfigManager 各字段，再查 v5.2 默认，最后给定默认）。"""
        # 优先走 ConfigManager 的专用 getter
        getter = self._getter_map().get(key)
        if getter is not None:
            try:
                return getter()
            except Exception:
                pass
        # 通用兜底：直接查 host_cfg/agent_cfg
        if key in self._mgr.host_cfg:
            return self._mgr.host_cfg.get(key)
        if key in self._mgr.agent_cfg:
            return self._mgr.agent_cfg.get(key)
        # v5.2 默认
        if key in V52_DEFAULTS:
            return V52_DEFAULTS[key]
        return default

    # ---------- 通用写 ----------

    def set(self, key: str, value) -> None:
        """按 key 写入配置（路由到 ConfigManager 专用 setter 或直接写字典）。"""
        setter = self._setter_map().get(key)
        if setter is not None:
            setter(value)
        else:
            # 未知 key：写入 host_cfg（保守），同时尝试 agent_cfg 若存在
            self._mgr.host_cfg[key] = value
            if key in self._mgr.agent_cfg:
                self._mgr.agent_cfg[key] = value
        self.settings_changed.emit(key)

    # ---------- 持久化 ----------

    def save(self) -> None:
        self._mgr.save_all()

    def save_agent(self) -> None:
        self._mgr.save_agent()

    def save_host(self) -> None:
        self._mgr.save_host()

    def reset(self, key: str | None = None) -> None:
        """重置配置（规格要求）。

        - key 给定：删除该 key（恢复为默认兜底）
        - key 为 None：重置 v5.2 新增字段为默认值
        """
        if key is not None:
            self._mgr.host_cfg.pop(key, None)
            self._mgr.agent_cfg.pop(key, None)
            self.settings_changed.emit(key)
            return
        for k, v in V52_DEFAULTS.items():
            if k in self._mgr.host_cfg:
                del self._mgr.host_cfg[k]
            if k in self._mgr.agent_cfg:
                del self._mgr.agent_cfg[k]
        self.settings_changed.emit("*")

    # ---------- 便捷 get/set 路由 ----------

    def _getter_map(self):
        m = self._mgr
        return {
            "language": m.get_language,
            "theme": m.get_theme,
            "ui_scale": m.get_ui_scale,
            "log_level": m.get_log_level,
            "debug_mode": m.get_debug_mode,
            "http_port": m.get_http_port,
            "udp_port": m.get_udp_port,
            "use_multicast": m.get_use_multicast,
            "preferred_iface": m.get_preferred_iface,
            "auto_discovery": m.get_auto_discovery,
            "auto_connect": m.get_auto_connect,
            "agent_auto_start": m.get_agent_auto_start,
            "host_auto_start": m.get_host_auto_start,
            "onboarded": m.get_onboarded,
        }

    def _setter_map(self):
        m = self._mgr
        return {
            "language": m.set_language,
            "theme": m.set_theme,
            "ui_scale": m.set_ui_scale,
            "log_level": m.set_log_level,
            "debug_mode": m.set_debug_mode,
            "http_port": m.set_http_port,
            "udp_port": m.set_udp_port,
            "use_multicast": m.set_use_multicast,
            "preferred_iface": m.set_preferred_iface,
            "auto_discovery": m.set_auto_discovery,
            "auto_connect": m.set_auto_connect,
            "agent_auto_start": m.set_agent_auto_start,
            "host_auto_start": m.set_host_auto_start,
            "onboarded": m.set_onboarded,
        }

    # ---------- 告警规则 ----------

    def get_alerts(self) -> list:
        """告警规则列表；未配置时回退内置默认。"""
        alerts = self._mgr.get_alerts()
        if not alerts:
            from host.config import DEFAULT_ALERTS
            return list(DEFAULT_ALERTS)
        return alerts

    def get_alert(self, path: str) -> dict | None:
        return self._mgr.get_alert(path)

    def set_alert(self, path: str, red=None, warn=None,
                  red_min=None, warn_min=None, name=None) -> None:
        self._mgr.set_alert(path, red=red, warn=warn,
                            red_min=red_min, warn_min=warn_min, name=name)
        self.settings_changed.emit(f"alert:{path}")

    # ---------- 节点列表 ----------

    def get_hosts(self) -> list:
        return self._mgr.get_hosts()

    def add_host(self, node_id, ip, port, token, alias="") -> None:
        self._mgr.add_host(node_id, ip, port, token, alias)
        self.settings_changed.emit("hosts")

    def remove_host(self, node_id) -> None:
        self._mgr.remove_host(node_id)
        self.settings_changed.emit("hosts")
