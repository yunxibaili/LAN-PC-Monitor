# -*- coding: utf-8 -*-
"""
v5.2 Controllers 层 —— MainWindow 业务逻辑拆分。

- NavigationController：页面切换（SideNav ↔ contentStack）
- DataController：WS 数据入口 + 节点增删 + 发现
- AlertController：告警通知（托盘/状态栏）
- WindowController：窗口几何/状态/关闭

注意：各 Controller 惰性导入（部分依赖 PyQt5，便于无 GUI 测试 DataController）。
"""
__all__ = [
    "NavigationController", "DataController",
    "AlertController", "WindowController",
]
