# -*- coding: utf-8 -*-
"""
v5.2 Host Facade 层 —— 供页面/Controller 使用的统一入口。

- SettingsFacade：包装现有 ConfigManager（SettingsManager 别名），统一配置读写。
- AlertAdapter：将 AlertEngine 输出桥接到 AlertStore。
"""
from host.facade.settings_facade import SettingsFacade  # noqa: F401
from host.facade.alert_adapter import AlertAdapter      # noqa: F401
from host.facade.connection_factory import create_connection  # noqa: F401

__all__ = ["SettingsFacade", "AlertAdapter", "create_connection"]
