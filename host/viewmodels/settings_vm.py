# -*- coding: utf-8 -*-
"""
SettingsViewModel —— Settings 页面数据桥接层（v5.2 Phase 3-6A）。

职责：
  - 包装 SettingsFacade，提供页面友好的读写接口
  - 配置即时生效（set → Facade → 磁盘）
  - 通知页面配置变更
  - 不持有 UI 状态
"""
import logging

from host.store.signals import Signal

log = logging.getLogger("host.viewmodels.settings_vm")


class SettingsViewModel:
    """Settings 数据桥接层：页面 ↔ Facade。"""

    settings_changed = Signal(str)  # key（单个字段变更）或 "*"（全量重置）

    def __init__(self, facade):
        """
        :param facade: SettingsFacade 实例（MainWindow 传入）
        """
        self._facade = facade

    # ---------- 基础配置 ----------

    def get(self, key: str, default=None):
        """按 key 读取配置值。"""
        return self._facade.get(key, default)

    def set(self, key: str, value) -> None:
        """即时写入配置（Facade 内存 + 磁盘）。"""
        self._facade.set(key, value)
        self._facade.save()
        self.settings_changed.emit(key)

    def reset(self, key: str | None = None) -> None:
        """重置配置（单字段或全量）。"""
        self._facade.reset(key)
        self._facade.save()
        self.settings_changed.emit(key or "*")

    def get_all(self) -> dict:
        """返回当前配置快照。"""
        keys = [
            "language", "theme", "ui_scale",
            "log_level", "debug_mode",
            "udp_port", "auto_discovery", "auto_connect",
            "alert_popup",
        ]
        return {k: self._facade.get(k) for k in keys}

    # ---------- 告警配置 ----------

    def get_alerts(self) -> list:
        """获取告警规则列表。"""
        # 从 ConfigManager 的 host_cfg 读取 alerts 字段
        mgr = self._facade._mgr
        alerts = getattr(mgr, 'host_cfg', {}).get("alerts", [])
        if not alerts:
            # 回退到内置默认告警（host/config.py DEFAULT_ALERTS）
            from host.config import DEFAULT_ALERTS
            alerts = list(DEFAULT_ALERTS)
        return alerts

    def set_alert(self, path: str, **kwargs) -> None:
        """更新单条告警规则。"""
        self._facade.set_alert(path, **kwargs)

    def reset_alerts(self) -> None:
        """恢复默认告警规则。"""
        self._facade.reset()
        self._facade.save()
        self.settings_changed.emit("alerts")

    # ---------- 节点配置 ----------

    def get_hosts(self) -> list:
        """获取节点列表。"""
        return self._facade.get_hosts()

    def add_host(self, node_id, ip, port, token, alias="") -> None:
        """添加节点。"""
        self._facade.add_host(node_id, ip, port, token, alias)
        self._facade.save()

    def remove_host(self, node_id) -> None:
        """移除节点。"""
        self._facade.remove_host(node_id)
        self._facade.save()

    # ---------- Facade 直通 ----------

    @property
    def facade(self):
        """直接访问 Facade（MainWindow 需要）。"""
        return self._facade
