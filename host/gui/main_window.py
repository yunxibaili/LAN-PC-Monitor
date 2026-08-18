# -*- coding: utf-8 -*-
"""
监控主机主窗口 —— v5.2 精简版（Phase 3-8）。

只负责：
  1. 创建 Store / Service / Manager
  2. 创建 ViewModel
  3. 注册 5 个页面（经 VM 注入）
  4. 创建 Controllers（navigation / data / alert / window）
  5. 连接 Signal（NodeConnection → DataController → Store → 页面）

不再包含：
  - legacy 顶部工具栏（概览/添加/扫描/连接码/剪贴板/导入/导出）
  - legacy detail_stack / splitter / node_list / detail_panel
  - overview 模式
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMainWindow,
                             QPushButton, QStackedWidget, QVBoxLayout,
                             QWidget)

from common.i18n import tr
from common.utils import get_lan_ip
from host import config as host_config
from host.alerts import AlertEngine
from common.constants import LOCAL_NODE_ID
from host.local_node import LocalCollectorPack

# Store / Service / Manager
from host.store.frame_store import FrameStore
from host.store.node_store import NodeStore
from host.store.history_store import HistoryStore
from host.store.alert_store import AlertStore
from host.facade.settings_facade import SettingsFacade
from host.service.alert_service import AlertService
from host.service.discovery_service import DiscoveryService
from host.manager.tray_manager import TrayManager

# v5.2 UI 框架
from host.gui.navigation.side_nav import SideNav
from host.gui.pages.dashboard_page import DashboardPage
from host.gui.pages.nodes_page import NodesPage
from host.gui.pages.monitor_page import MonitorPage
from host.gui.pages.alerts_page import AlertsPage
from host.gui.pages.history_page import HistoryPage
from host.gui.pages.settings_page import SettingsPage

# ViewModels
from host.viewmodels.dashboard_vm import DashboardViewModel
from host.viewmodels.node_detail_vm import NodeDetailViewModel
from host.viewmodels.settings_vm import SettingsViewModel
from host.viewmodels.history_vm import HistoryViewModel
from host.viewmodels.devices_vm import DevicesViewModel
from host.facade.history_facade import HistoryFacade
from host.service.storage_service import StorageService
from host.service.metric_persistence import MetricPersistenceService

# Controllers
from host.gui.controllers.navigation_controller import NavigationController
from host.gui.controllers.data_controller import DataController
from host.gui.controllers.alert_controller import AlertController
from host.gui.controllers.window_controller import WindowController

log = logging.getLogger("host.gui.main_window")

MODE_AUTO = "auto"


class HostMainWindow(QMainWindow):
    """监控主机主窗口（v5.2 精简版）。"""

    # ---------- Store 单一来源（property 代理，兼容旧代码/测试） ----------

    @property
    def frames(self):
        return self.frame_store._frames

    @property
    def statuses(self):
        return self.node_store._statuses

    @property
    def rtts(self):
        return self.node_store._rtts

    @property
    def losses(self):
        return self.node_store._losses

    @property
    def scores(self):
        return self.node_store._scores

    @property
    def scorers(self):
        return self.node_store._scorers

    # ---------- 生命周期 ----------

    def __init__(self, cfg: dict = None):
        super().__init__()
        self.cfg = cfg or host_config.load_config()
        self.current_node = None

        # 1. 创建 Store / Service / Manager
        self.settings = SettingsFacade()
        self.frame_store = FrameStore()
        self.node_store = NodeStore()
        self.history_store = HistoryStore(maxlen=300)
        self.alert_store = AlertStore(dedup_seconds=30)
        self.alert_service = AlertService(
            AlertEngine(host_config.load_alerts(self.cfg)),
            frame_store=self.frame_store,
            alert_store=self.alert_store,
            node_store=self.node_store,
            auto_subscribe=True)
        self.alert_engine = self.alert_service.engine
        self.tray_manager = TrayManager(icon_color="ThemeColors.PRIMARY")
        self.discovery = DiscoveryService(
            udp_port=self.cfg.get("udp_port", 12346), auto_start=False)
        # 兼容引用（旧对话框使用）
        self.listener = self.discovery._listener
        self.mdns = self.discovery._mdns

        # 2. 创建 UI 骨架
        self._init_ui()

        # 3. 创建 ViewModels
        self._init_viewmodels()

        # 4. 创建 Controllers
        self._init_controllers()

        # 5. 启动
        self.tray_manager.init(tooltip=tr("app.title.host"))
        self._init_local_node()
        self.discovery.start()
        if self.cfg.get("auto_discovery", True):
            self.data.auto_discover()
        self._run_startup_retention()
        log.info("监控主机主窗口已创建（v5.2）")

    def _run_startup_retention(self) -> None:
        """应用启动时执行一次数据保留清理（不轮询、不后台线程）。"""
        try:
            result = self._storage.run_retention()
            log.info("Startup retention: %s", result)
        except Exception as e:
            log.warning("Startup retention failed: %s", e)

    # ---------- UI 骨架 ----------

    def _init_ui(self) -> None:
        """构建 v5.2 布局：HeaderBar + SideNav + contentStack。"""
        self.setWindowTitle(tr("app.title.host"))
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 顶部 HeaderBar
        from host.gui.widgets.header_bar import HeaderBar
        self.header_bar = HeaderBar()
        self.header_bar.settings_clicked.connect(
            lambda: self.nav.navigate_to("settings"))
        self._header_title = self.header_bar._title
        self.top_label = self.header_bar._conn_label  # 兼容旧代码引用
        root.addWidget(self.header_bar)

        # 主体：SideNav + contentStack
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        self.side_nav = SideNav()
        body.addWidget(self.side_nav)
        self.content_stack = QStackedWidget()
        body.addWidget(self.content_stack, 1)
        root.addLayout(body, 1)

        self.setCentralWidget(central)
        self.statusBar().showMessage(tr("topbar.ready"))

    # ---------- ViewModels + Pages ----------

    def _init_viewmodels(self) -> None:
        """创建 ViewModel 并注入对应页面。"""
        self.dashboard_vm = DashboardViewModel(
            node_store=self.node_store, frame_store=self.frame_store)
        self.node_detail_vm = NodeDetailViewModel(
            node_store=self.node_store, frame_store=self.frame_store)
        self.settings_vm = SettingsViewModel(self.settings)
        self.devices_vm = DevicesViewModel(self.node_store, self.frame_store)

        # Storage Service（统一管理 SQLite 连接 + Repository）
        # v5.3.1：默认路径固定到用户数据目录，不再跟随启动 CWD
        self._storage = StorageService()
        # 5-5C: 从配置加载 retention 策略
        from host.storage.retention import RetentionPolicy
        ret_policy = RetentionPolicy(
            metrics_days=self.cfg.get("retention_metrics", 30),
            alerts_days=self.cfg.get("retention_alerts", 90),
            sessions_days=self.cfg.get("retention_sessions", 90),
        )
        self._storage.retention_service(ret_policy).run()
        self._history_facade = self._storage.history_facade()
        self.history_vm = HistoryViewModel(self._history_facade)
        self._metric_persistence = MetricPersistenceService(
            self._storage.metrics_repo)

        # Pages
        self._pages = {}
        for PageClass in (DashboardPage, NodesPage, MonitorPage,
                          AlertsPage, HistoryPage, SettingsPage):
            page = PageClass()
            page.set_stores(frame=self.frame_store, node=self.node_store,
                            history=self.history_store, alert=self.alert_store)
            page.set_facade(self.settings)
            self._pages[PageClass.PAGE_ID] = page
            self.content_stack.addWidget(page)

        # VM 注入
        self.dashboard_page = self._pages["dashboard"]
        self.dashboard_page.set_view_model(self.dashboard_vm)
        self.dashboard_page.set_frame_store(self.frame_store)
        self.dashboard_page.set_alert_store(self.alert_store)
        self.dashboard_page.card_clicked.connect(self._on_card_clicked)

        self.nodes_page = self._pages["nodes"]
        self.nodes_page.set_view_model(self.devices_vm)

        self.monitor_page = self._pages["monitor"]
        self.alerts_page = self._pages["alerts"]
        self.history_page = self._pages["history"]
        self.history_page.set_view_model(self.history_vm)
        self.settings_page = self._pages["settings"]
        self.settings_page.set_view_model(self.settings_vm)

    # ---------- Controllers ----------

    def _init_controllers(self) -> None:
        """创建 Controllers 并接线。"""
        self.nav = NavigationController(self.side_nav, self.content_stack,
                                        self._pages)
        self.nav.connect_signals(header_title=self._header_title)

        self.data = DataController(
            self.cfg, self.frame_store, self.node_store, self.history_store,
            self.discovery,
            persistence=self._metric_persistence,
            on_node_added=self._on_node_ui_added,
            on_node_removed=self._on_node_ui_removed)
        self.data.set_callbacks(
            on_data=self._on_frame_cb,
            on_status=self._on_status_cb,
            on_rtt=self._on_rtt_cb,
            on_loss=self._on_loss_cb)

        self.alert = AlertController(self.alert_store, self.tray_manager,
                                     self.cfg)
        self.alert.connect(status_bar=self.statusBar())

        self.window_ctrl = WindowController(
            self.cfg, self, discovery=self.discovery,
            alert_service=self.alert_service, data_controller=self.data,
            tray_manager=self.tray_manager)
        self.window_ctrl.restore_geometry()

    # ---------- 本机节点 ----------

    def _init_local_node(self) -> None:
        self.local_pack = LocalCollectorPack(self.cfg)
        self.local_pack.local_data.connect(self._on_local_data)
        self.local_pack.start()
        self.data.init_local_node(alias=tr("node.local_alias"))
        local_ip = get_lan_ip(self.cfg.get("preferred_iface", ""))
        self.side_nav.add_node(LOCAL_NODE_ID, tr("node.local_alias"))
        log.info("本机节点已初始化（IP=%s）", local_ip)

    # ---------- Signal → Store → UI 回调 ----------

    def _on_local_data(self, frame: dict, node_id: str) -> None:
        self.data._on_data(frame, node_id)

    def _on_frame_cb(self, frame: dict, node_id: str) -> None:
        """每帧回调：Dashboard 趋势 + 告警状态栏。"""
        self.dashboard_page.update_trends(node_id, frame)
        self.alert.refresh_status_bar(node_id)

    def _on_status_cb(self, status: str, node_id: str) -> None:
        self.side_nav.update_node_status(node_id, status)
        self.side_nav.update_node_title(len(self.data.connected_node_ids()),
                                        len(self.data.nodes))
        self.top_label.setText(tr("topbar.connected",
                                  len(self.data.connected_node_ids()),
                                  len(self.data.nodes)))
        self.statusBar().showMessage(
            f"{self.data.nodes[node_id].alias}: {status}", 3000)

    def _on_rtt_cb(self, rtt_ms: float, node_id: str) -> None:
        pass  # RTT 已入 NodeStore；页面经 VM 读取

    def _on_loss_cb(self, loss: float, node_id: str) -> None:
        pass  # 丢包已入 NodeStore

    # ---------- UI 节点同步 ----------

    def _on_node_ui_added(self, node_id: str, conn) -> None:
        self.side_nav.add_node(node_id, conn.alias)
        self.top_label.setText(tr("topbar.connected",
                                  len(self.data.connected_node_ids()),
                                  len(self.data.nodes)))

    def _on_node_ui_removed(self, node_id: str) -> None:
        self.side_nav.remove_node(node_id)
        self.top_label.setText(tr("topbar.connected",
                                  len(self.data.connected_node_ids()),
                                  len(self.data.nodes)))

    # ---------- 导航回调 ----------

    def _on_card_clicked(self, node_id: str) -> None:
        self.nav.navigate_to_node(node_id)

    def _on_node_selected_vm(self, node_id: str) -> None:
        self.current_node = node_id

    # ---------- 窗口事件 ----------

    def closeEvent(self, event) -> None:
        self.window_ctrl.shutdown()
        if self.local_pack:
            self.local_pack.stop()
        self.alert.shutdown()
        if getattr(self, "_storage", None):
            self._storage.close()
        event.accept()
