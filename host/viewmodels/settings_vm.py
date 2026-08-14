# -*- coding: utf-8 -*-
"""
SettingsViewModel —— Settings 页面数据桥接层（v5.2 Phase 3-6A / 4-6A）。

职责：
  - 包装 SettingsFacade，提供页面友好的读写接口
  - 配置写入只改内存 + 标 dirty，持久化统一走 save()
  - 通知页面配置变更
  - 不持有 UI 状态
  - 不暴露 Facade（Page 不允许获取 Facade 实例）
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
        self._dirty = False

    # ---------- Dirty State ----------

    def is_dirty(self) -> bool:
        """是否有未保存的变更。"""
        return self._dirty

    def _mark_dirty(self):
        self._dirty = True

    def _clear_dirty(self):
        self._dirty = False

    # ---------- 基础配置 ----------

    def get(self, key: str, default=None):
        """按 key 读取配置值。"""
        return self._facade.get(key, default)

    def set(self, key: str, value) -> None:
        """写入配置内存（不持久化；保存统一走 save()）。"""
        self._facade.set(key, value)
        self._mark_dirty()
        self.settings_changed.emit(key)

    def save(self) -> None:
        """持久化全部配置（一次写盘）。"""
        self._facade.save()
        self._clear_dirty()

    def reset(self, key: str | None = None) -> None:
        """重置配置（单字段或全量；保存走 save()）。"""
        self._facade.reset(key)
        self._mark_dirty()
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
        """获取告警规则列表（走 Facade）。"""
        return self._facade.get_alerts()

    def get_alert(self, path: str):
        """按指标路径取单条告警规则。"""
        return self._facade.get_alert(path)

    def set_alert(self, path: str, **kwargs) -> None:
        """更新单条告警规则（内存；保存走 save()）。"""
        self._facade.set_alert(path, **kwargs)
        self._mark_dirty()

    def reset_alerts(self) -> None:
        """恢复默认告警规则（内存；保存走 save()）。"""
        self._facade.reset()
        self._mark_dirty()
        self.settings_changed.emit("alerts")

    # ---------- 节点配置 ----------

    def get_hosts(self) -> list:
        """获取节点列表。"""
        return self._facade.get_hosts()

    def add_host(self, node_id, ip, port, token, alias="") -> None:
        """添加节点（内存；保存走 save()）。"""
        self._facade.add_host(node_id, ip, port, token, alias)
        self._mark_dirty()

    def remove_host(self, node_id) -> None:
        """移除节点（内存；保存走 save()）。"""
        self._facade.remove_host(node_id)
        self._mark_dirty()
