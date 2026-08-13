# -*- coding: utf-8 -*-
"""
TrayManager —— 系统托盘管理（v5.2 Phase 0）。

职责：将 v5.1 内联在 HostMainWindow 的托盘逻辑（`_init_tray` / 告警气泡 /
最小化到托盘）独立封装。无 QSystemTrayIcon 环境时静默降级。

- 提供 init / show_message / set_visible / shutdown 接口。
- 菜单：显示主窗口 / 退出（由回调注入，避免依赖具体窗口）。
- 不修改现有 HostMainWindow 托盘功能；为 v5.2 页面化重构预留。
"""
import logging
import os
import sys

from host.gui.theme.colors import ThemeColors as TC

log = logging.getLogger("host.manager.tray")

try:
    from PyQt5.QtGui import QColor, QIcon, QPixmap
    from PyQt5.QtWidgets import QMenu, QSystemTrayIcon
    _HAS_TRAY = True
except ImportError:
    _HAS_TRAY = False


def _is_headless() -> bool:
    """检测无显示环境（无系统托盘），避免调用 isSystemTrayAvailable 触发原生崩溃。

    说明：在 offscreen/minimal 等无显示 Qt 平台上，
    QSystemTrayIcon.isSystemTrayAvailable() 可能直接段错误（Python 无法捕获）。
    通过显式平台检查 + 显示服务器探测，无显示环境直接降级禁用托盘。
    """
    qpa = os.environ.get("QT_QPA_PLATFORM", "").lower()
    if qpa in ("offscreen", "minimal", "minimalegl", "headless", "vnc"):
        return True
    if sys.platform == "win32" or sys.platform == "darwin":
        return False
    # Linux/其他：必须有显示服务器
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return True
    return False


class TrayManager:
    """系统托盘管理（不可用时降级为 None 能力）。"""

    def __init__(self, on_show=None, on_quit=None, icon_color: str = TC.ACCENT_PRIMARY):
        """
        :param on_show:   菜单"显示"回调（如 window.show/raise_）
        :param on_quit:   菜单"退出"回调（如 app.quit）
        :param icon_color: 无图标时的占位色
        """
        self.on_show = on_show
        self.on_quit = on_quit
        self._tray = None
        self._menu = None
        self._icon_color = icon_color
        self._available = False

    # ---------- 生命周期 ----------

    def init(self, tooltip: str = "") -> bool:
        """初始化托盘。返回是否成功（不可用时返回 False）。"""
        if not _HAS_TRAY:
            log.debug("PyQt5 不可用，系统托盘降级禁用")
            return False
        if _is_headless():
            log.debug("无显示环境（headless），系统托盘降级禁用")
            return False
        try:
            if not QSystemTrayIcon.isSystemTrayAvailable():
                log.debug("系统托盘不可用，降级禁用")
                return False
            self._tray = QSystemTrayIcon()
            self._tray.setIcon(self._make_icon())
            if tooltip:
                self._tray.setToolTip(tooltip)
            self._menu = QMenu()
            if self.on_show:
                act = self._menu.addAction("Show")
                act.triggered.connect(lambda: self._call(self.on_show))
            if self.on_quit:
                act = self._menu.addAction("Quit")
                act.triggered.connect(lambda: self._call(self.on_quit))
            if self._menu:
                self._tray.setContextMenu(self._menu)
            self._tray.show()
            self._available = True
            return True
        except Exception as e:
            log.debug("系统托盘初始化失败: %s", e)
            self._tray = None
            return False

    def shutdown(self) -> None:
        """隐藏并释放托盘。"""
        if self._tray is not None:
            try:
                self._tray.hide()
            except Exception:
                pass
            self._tray = None
        self._available = False

    # ---------- 对外能力 ----------

    @property
    def available(self) -> bool:
        return self._available

    def show_message(self, title: str, message: str,
                     icon="info", timeout_ms: int = 3000) -> None:
        """托盘气泡提示。不可用时静默。"""
        if self._tray is None:
            return
        try:
            icon_type = (QSystemTrayIcon.Information if icon == "info"
                         else QSystemTrayIcon.Warning if icon == "warning"
                         else QSystemTrayIcon.Critical)
            self._tray.showMessage(title, message, icon_type, timeout_ms)
        except Exception:
            pass

    # ---------- 内部 ----------

    def _make_icon(self):
        """生成占位图标（无 PyQt5 时此方法不会被调用）。"""
        if not _HAS_TRAY:
            return None
        pm = QPixmap(16, 16)
        pm.fill(QColor(self._icon_color))
        return QIcon(pm)

    @staticmethod
    def _call(fn):
        try:
            fn()
        except Exception:
            log.debug("托盘回调异常", exc_info=True)
