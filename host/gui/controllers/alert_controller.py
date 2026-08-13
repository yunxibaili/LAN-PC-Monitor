# -*- coding: utf-8 -*-
"""
AlertController —— 告警通知控制（v5.2 Phase 3-8）。

职责：
  - 订阅 AlertStore.alert_added → 日志 + 托盘气泡
  - 状态栏告警展示（读 AlertStore 当前活动告警）
  - 托盘管理（TrayManager）

不访问 Store 内部；通过 AlertStore 信号驱动。
"""
import logging

from common.i18n import tr
from host.gui.theme.colors import ThemeColors as TC
from host.manager.tray_manager import TrayManager

log = logging.getLogger("host.gui.controllers.alert")


class AlertController:
    """告警通知控制器。"""

    def __init__(self, alert_store, tray_manager: TrayManager, cfg: dict):
        self.alert_store = alert_store
        self.tray = tray_manager
        self.cfg = cfg
        self._status_bar = None
        self._subscribed = False

    # ---------- 连接 ----------

    def connect(self, status_bar=None) -> None:
        """订阅告警信号。"""
        self._status_bar = status_bar
        if not self._subscribed:
            self.alert_store.alert_added.connect(self._on_alert_added)
            self._subscribed = True

    def disconnect(self) -> None:
        if self._subscribed:
            self.alert_store.alert_added.disconnect(self._on_alert_added)
            self._subscribed = False

    # ---------- 信号回调 ----------

    def _on_alert_added(self, alert: dict) -> None:
        """新增告警（去重后触发一次）→ 日志 + 托盘。"""
        if alert.get("level") == "red":
            log.warning("[alert] %s %s=%s 超红线 %s",
                        alert.get("name"), alert.get("path"),
                        alert.get("value"), alert.get("threshold"))
            self._show_tray_alert(alert)
        elif alert.get("level") == "warn":
            log.info("[alert] %s %s=%s 达预警 %s",
                     alert.get("name"), alert.get("path"),
                     alert.get("value"), alert.get("threshold"))

    def refresh_status_bar(self, node_id: str) -> None:
        """从 AlertStore 当前活动告警刷新状态栏。"""
        if self._status_bar is None:
            return
        node_alerts = self.alert_store.node_alerts(node_id)
        if not node_alerts:
            self._status_bar.showMessage(tr("topbar.ready"), 3000)
            return
        red = [a for a in node_alerts if a["level"] == "red"]
        warn = [a for a in node_alerts if a["level"] == "warn"]
        if red:
            text = tr("alert.red_summary", red[0]["name"], red[0]["value"])
            self._status_bar.setStyleSheet(f"color: {TC.STATUS_ERROR}; font-weight: bold;")
            self._status_bar.showMessage(text)
        elif warn:
            text = tr("alert.warn_summary", warn[0]["name"], warn[0]["value"])
            self._status_bar.setStyleSheet(f"color: {TC.STATUS_WARNING}; font-weight: bold;")
            self._status_bar.showMessage(text)

    def _show_tray_alert(self, alert: dict) -> None:
        """托盘气泡（red 首次触发）。"""
        if not self.tray.available:
            return
        if not self.cfg.get("alert_popup", True):
            return
        try:
            self.tray.show_message(
                tr("alert.tray_title"),
                tr("alert.tray_body", alert["name"], alert["value"],
                   alert["threshold"]),
                icon="warning", timeout_ms=5000)
        except Exception as e:
            log.debug("托盘气泡显示失败: %s", e)

    def shutdown(self) -> None:
        self.disconnect()
