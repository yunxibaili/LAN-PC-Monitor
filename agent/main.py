# -*- coding: utf-8 -*-
"""
Agent 入口模块（见《README.md》§5.1）。

启动流程：
1. 解析命令行参数（--install-startup / --remove-startup / --gui / 普通启动）
2. 单实例检测（Global\\PC_Monitor_Agent）
3. 初始化日志 → logs/agent.log
4. 加载配置 agent_config.json
5. 端口占用检测（HTTP/WS 12345 / UDP 12346）
6. 启动采集器线程池
7. 启动数据聚合器（1 秒 → 最新帧缓存）
8. 启动 aiohttp 应用：REST /api/* + WebSocket /ws（同端口）
9. 启动 WS 推送协程（每秒广播最新帧）
10. 启动 UDP/mDNS 广播器（自动发现，可选）
11. 进入 asyncio 事件循环（等退出信号）

两种运行方式：
- **默认（后台）**：不创建 QApplication、不弹窗口，可用 pythonw.exe 启动。
- **`--gui`（仪表盘）**：同一进程内弹出本机仪表盘（PyQt5），
  后台 asyncio 服务在 QThread 中运行；关闭窗口即退出服务。
"""
import argparse
import asyncio
import logging
import signal
import socket
import sys
import threading

from aiohttp import web

from agent import config as agent_config
from agent.aggregator import DataAggregator
from agent.http_server import RestServer
from agent.websocket_server import WebSocketServer
from agent.discovery import DiscoveryBroadcaster, register_mdns, unregister_mdns
from common.collectors import create_collectors, start_all, stop_all
from common.logger import setup_logger
from common.single_instance import ensure_single_instance, release_single_instance
from common.startup import (install_agent_startup, remove_agent_startup)
from common.utils import get_lan_ip, check_port_in_use

# 全局退出事件
_stop_event = None


def parse_args():
    parser = argparse.ArgumentParser(
        description="副机端 Agent：采集 + WebSocket/REST 服务（后台，可选本机仪表盘）")
    parser.add_argument("--install-startup", action="store_true",
                        help="安装开机自启动（需管理员，schtasks）")
    parser.add_argument("--remove-startup", action="store_true",
                        help="卸载开机自启动")
    parser.add_argument("--gui", action="store_true",
                        help="弹出本机仪表盘 GUI（PyQt5），后台服务同进程运行（管理员模式）")
    parser.add_argument("--tray", action="store_true",
                        help="系统托盘模式（默认后台无界面；--tray 增加托盘图标，可打开仪表盘/退出）")
    return parser.parse_args()


# ---------- 后台服务（可运行在线程/事件循环） ----------

class AgentService:
    """封装 Agent 后台服务生命周期：可在 asyncio 主循环或 QThread 中运行。"""

    def __init__(self, cfg, log):
        self.cfg = cfg
        self.log = log
        self.collectors = None
        self.aggregator = None
        self.ws_server = None
        self.rest_server = None
        self.runner = None
        self.site = None
        self.broadcaster = None
        self.mdns_zc = None
        self.self_monitor = None
        self.loop = None

    def start(self) -> None:
        """同步启动：创建采集器/聚合器/服务（不阻塞）。"""
        self.collectors = create_collectors(self.cfg)
        start_all(self.collectors)

        self.aggregator = DataAggregator(collectors=self.collectors)
        self.aggregator.start()

        self.ws_server = WebSocketServer(token=self.cfg["token"],
                                         aggregator=self.aggregator)
        self.aggregator.set_subscriber_counter(self.ws_server.subscriber_count)

        self.rest_server = RestServer(cfg=self.cfg, aggregator=self.aggregator)

        app = self.rest_server.make_app()
        app.router.add_get("/ws", self.ws_server.ws_handler)

        from agent.self_monitor import SelfMonitor
        self.self_monitor = SelfMonitor(self.aggregator, self.collectors)
        self.self_monitor.start()

        self.broadcaster = DiscoveryBroadcaster(
            http_port=self.cfg["http_port"], udp_port=self.cfg["udp_port"],
            token=self.cfg["token"],
            use_multicast=self.cfg.get("use_multicast", False),
            preferred_iface=self.cfg.get("preferred_iface", ""))
        self.broadcaster.start()
        lan_ip = get_lan_ip(self.cfg.get("preferred_iface", ""))
        self.mdns_zc = register_mdns(lan_ip, self.cfg["http_port"],
                                     socket.gethostname(), self.cfg["token"])
        self.app = app

        # P2-4: stdout 不打印 token（安全）；日志脱敏，完整连接串不落盘
        print(f"\n  Agent 已启动: http://{lan_ip}:{self.cfg['http_port']}\n")
        print(f"  Token 已保存到 agent_config.json（连接时请查看配置文件）\n")
        self.log.info("Agent 连接串: pcmonitor://%s:%d?token=%s",
                      lan_ip, self.cfg["http_port"], "***")
        self.log.info("Agent 服务已启动（HTTP/WS %d, UDP %d）",
                      self.cfg["http_port"], self.cfg["udp_port"])

    async def _serve(self) -> None:
        """异步启动 HTTP/WS 服务并保持。

        注意：push_loop 必须在事件循环内启动（start_push_loop 用 asyncio.ensure_future），
        否则 task 不会被调度。
        """
        self.ws_server.start_push_loop()
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "0.0.0.0", self.cfg["http_port"])
        await self.site.start()
        self.log.info("HTTP/WebSocket 服务已启动 0.0.0.0:%d", self.cfg["http_port"])

    async def _wait_stop(self, stop_event: asyncio.Event) -> None:
        await stop_event.wait()

    def stop(self) -> None:
        """同步停止：清理全部资源。"""
        if self.self_monitor:
            self.self_monitor.stop()
        if self.aggregator:
            self.aggregator.stop()
        if self.collectors:
            stop_all(self.collectors)
        if self.broadcaster:
            self.broadcaster.stop()
        if self.mdns_zc:
            unregister_mdns(self.mdns_zc)
        self.log.info("Agent 服务已停止")

    def get_service_info(self) -> dict:
        """供 GUI 显示的后台服务状态。"""
        subs = self.ws_server.subscriber_count() if self.ws_server else 0
        return {"subscribers": subs}


def _run_service_blocking(cfg, log, stop_event: asyncio.Event,
                          service_ref: dict | None = None,
                          register_signals: bool = False) -> None:
    """在独立事件循环中运行 Agent 服务（供 GUI 线程/后台线程调用）。

    :param service_ref:       可选共享 dict，运行期间填入 "svc"（供 GUI 查询状态）
    :param register_signals:  True 时在事件循环内注册 SIGINT/SIGTERM → stop_event
                             （后台模式用；GUI 线程不能注册信号）
    """
    svc = AgentService(cfg, log)
    svc.start()
    if service_ref is not None:
        service_ref["svc"] = svc

    async def _amain():
        if register_signals:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(sig, stop_event.set)
                except NotImplementedError:
                    pass
        await svc._serve()
        await svc._wait_stop(stop_event)

    try:
        asyncio.run(_amain())
    except Exception as e:
        log.warning("Agent 服务异常退出: %s", e)
    finally:
        if service_ref is not None:
            service_ref.pop("svc", None)
        svc.stop()


def main() -> int:
    args = parse_args()
    if args.install_startup:
        ok = install_agent_startup()
        return 0 if ok else 1
    if args.remove_startup:
        ok = remove_agent_startup()
        return 0 if ok else 1

    # 单实例检测
    mutex = ensure_single_instance("Global\\PC_Monitor_Agent")
    if mutex is None:
        print("已有 Agent 实例在运行，退出。")
        return 1

    # 初始化日志
    log = setup_logger("agent")
    log.info("====== Agent 启动 ======")

    # 加载配置
    cfg = agent_config.load_config()
    log.info("HTTP/WS 端口 %d, UDP 端口 %d", cfg["http_port"], cfg["udp_port"])

    # 端口占用检测（§5.1 步骤 5）
    if check_port_in_use(cfg["http_port"], "tcp"):
        print(f"错误: 端口 {cfg['http_port']} 已被占用，请检查是否已有 Agent 实例运行。")
        return 1
    if check_port_in_use(cfg["udp_port"], "udp"):
        print(f"错误: UDP 端口 {cfg['udp_port']} 已被占用。")
        return 1

    if args.gui:
        rc = _run_gui(cfg, log)
        release_single_instance(mutex)
        return rc

    if args.tray:
        rc = _run_tray(cfg, log)
        release_single_instance(mutex)
        return rc

    # ---- 后台模式（默认）----
    try:
        _run_background(cfg, log)
    except KeyboardInterrupt:
        pass
    finally:
        release_single_instance(mutex)
    return 0


def _run_tray(cfg, log) -> int:
    """托盘模式：后台服务 + 系统托盘图标（v5.1 Desktop Experience）。

    无 QSystemTrayIcon 环境（无 PyQt5）时降级为纯后台。
    托盘菜单：打开仪表盘 / 退出。
    """
    try:
        from PyQt5.QtCore import QThread
        from PyQt5.QtWidgets import QApplication, QMenu, QSystemTrayIcon
    except ImportError:
        log.warning("--tray 需要 PyQt5，降级为纯后台模式")
        _run_background(cfg, log)
        return 0

    from common.i18n import ensure_language
    from common.theme import DARK_QSS

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)
    ensure_language(cfg, agent_config.save_config, parent=app)

    # P1-5 fix: 先检测托盘可用性，不可用则单进程后台（避免双服务冲突）
    if not QSystemTrayIcon.isSystemTrayAvailable():
        log.warning("系统托盘不可用，降级为纯后台（单进程）")
        _run_background(cfg, log)
        return 0

    # 后台服务线程（仅在有托盘时启动）
    stop_event = asyncio.Event()
    service_ref = {}

    class _ServiceThread(QThread):
        def run(self):
            _run_service_blocking(cfg, log, stop_event, service_ref)

    svc_thread = _ServiceThread()
    svc_thread.start()

    tray = QSystemTrayIcon()
    tray.setToolTip("LAN PC Monitor - Agent")
    menu = QMenu()
    act_open = menu.addAction(tr("tray.open_dashboard"))
    menu.addSeparator()
    act_exit = menu.addAction(tr("tray.exit"))
    tray.setContextMenu(menu)

    # 打开仪表盘：与 --gui 相同，但复用当前服务
    dashboard_windows = {}

    def _open_dashboard():
        from agent.gui.main_window import AgentDashboardWindow
        if "main" in dashboard_windows and dashboard_windows["main"].isVisible():
            dashboard_windows["main"].raise_()
            return
        win = AgentDashboardWindow(
            cfg,
            service_info_getter=lambda: _service_status(service_ref),
            on_close=stop_event.set)
        win.show()
        dashboard_windows["main"] = win

    act_open.triggered.connect(_open_dashboard)
    act_exit.triggered.connect(app.quit)

    tray.show()
    # 首次托盘提示
    try:
        tray.showMessage("LAN PC Monitor",
                         tr("tray.agent_running"),
                         QSystemTrayIcon.Information, 3000)
    except Exception:
        pass

    log.info("Agent 托盘模式运行中")
    ret = app.exec_()

    stop_event.set()
    svc_thread.wait(3000)
    return ret


def _run_background(cfg, log) -> None:
    """后台模式：信号驱动的事件循环。

    asyncio.run() 内部创建事件循环；SIGINT/SIGTERM 在循环内注册
    （loop.add_signal_handler → stop_event），使 _wait_stop 返回后清理退出。
    """
    stop_event = asyncio.Event()
    _run_service_blocking(cfg, log, stop_event, register_signals=True)


def _run_gui(cfg, log) -> int:
    """GUI 模式：Qt 主循环 + 后台服务 QThread。"""
    try:
        from PyQt5.QtCore import QThread
        from PyQt5.QtWidgets import QApplication
    except ImportError:
        print("错误: --gui 需要 PyQt5。请安装 PyQt5 或改用后台模式（python -m agent）。")
        return 1

    from common.i18n import ensure_language
    from common.theme import DARK_QSS
    from agent.gui.main_window import AgentDashboardWindow

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)
    ensure_language(cfg, agent_config.save_config, parent=app)

    # 后台服务线程（asyncio）
    stop_event = asyncio.Event()
    # 线程安全的服务引用（GUI 读取订阅者数）
    service_ref = {}

    class _ServiceThread(QThread):
        def run(self):
            _run_service_blocking(cfg, log, stop_event, service_ref)

    svc_thread = _ServiceThread()
    svc_thread.start()

    window = AgentDashboardWindow(
        cfg,
        service_info_getter=lambda: _service_status(service_ref),
        on_close=stop_event.set)
    window.show()

    ret = app.exec_()
    # 关闭后停止服务线程
    stop_event.set()
    svc_thread.wait(3000)
    return ret


def _service_status(service_ref: dict) -> dict:
    """返回后台服务状态（供 GUI）。"""
    svc = service_ref.get("svc")
    if svc:
        return svc.get_service_info()
    return {"subscribers": 0}


if __name__ == "__main__":
    sys.exit(main())
