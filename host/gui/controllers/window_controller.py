# -*- coding: utf-8 -*-
"""
WindowController —— 窗口状态控制（v5.2 Phase 3-8）。

职责：
  - 窗口几何恢复/保存
  - 选中节点/视图模式状态记忆
  - 关闭时清理（委托各 Service/Manager）
"""
import logging

from common.i18n import tr
from host import config as host_config

log = logging.getLogger("host.gui.controllers.window")

MODE_AUTO = "auto"
MODE_OVERVIEW = "overview"


class WindowController:
    """窗口生命周期/状态控制器。"""

    def __init__(self, cfg: dict, main_window,
                 discovery=None, alert_service=None, data_controller=None,
                 tray_manager=None):
        """
        :param cfg:            host_config 字典
        :param main_window:    QMainWindow 实例
        :param discovery:      DiscoveryService
        :param alert_service:  AlertService
        :param data_controller:DataController
        :param tray_manager:   TrayManager
        """
        self.cfg = cfg
        self.window = main_window
        self.discovery = discovery
        self.alert_service = alert_service
        self.data = data_controller
        self.tray = tray_manager
        self.view_mode = self.cfg.get("view_mode", MODE_AUTO)

    # ---------- 几何 ----------

    def restore_geometry(self) -> None:
        g = self.cfg.get("window_geometry", {})
        self.window.setGeometry(g.get("x", 100), g.get("y", 100),
                                g.get("w", 1400), g.get("h", 900))

    def save_geometry(self) -> None:
        geo = self.window.geometry()
        self.cfg["window_geometry"] = {
            "x": geo.x(), "y": geo.y(), "w": geo.width(), "h": geo.height(),
        }
        host_config.save_config(self.cfg)

    def save_state(self) -> None:
        """保存选中节点/视图模式/几何。"""
        self.cfg["last_selected_node"] = (self.data.current_node
                                          if self.data else "") or ""
        self.cfg["view_mode"] = self.view_mode
        self.save_geometry()

    # ---------- 关闭 ----------

    def shutdown(self) -> None:
        """关闭时清理全部资源。"""
        if self.discovery:
            self.discovery.stop()
        if self.alert_service:
            self.alert_service.shutdown()
        if self.data:
            for conn in list(self.data.nodes.values()):
                if conn:
                    conn.stop()
        if self.tray:
            self.tray.shutdown()
        self.save_state()
