# Phase 3-8：MainWindow 架构瘦身

> **Version**: v5.2
> **Status**: 完成
> **日期**: 2026-08-12
> **目标**: 将 `host/gui/main_window.py` 从 v5.1 混合体瘦身为纯生命周期层（311 行），删除 legacy UI（顶部工具栏 / `_build_ui` / detail_stack / overview_grid），页面全部经 ViewModel 注入。

---

## 一、MainWindow 最终职责

`host/gui/main_window.py`（**311 行**，目标 ≤400）

```python
class HostMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._init_ui()              # Header + SideNav + contentStack 骨架
        self._init_viewmodels()      # 5 个 VM + 5 个页面注册（经 VM 注入）
        self._init_controllers()     # navigation / data / alert / window
        self._init_local_node()      # 本机采集
        self._connect_signals()      # 数据回调 → Store → 页面
```

**已删除**：
- legacy 顶部工具栏（概览/添加节点/扫描/连接码/剪贴板/导入/导出）
- `_build_ui()` 整套 legacy 布局
- legacy detail_stack / splitter / node_list / detail_panel
- overview 模式切换（`_apply_view_mode` / `_on_toggle_overview`）

**功能迁移**：

| 功能 | 去向 |
|------|------|
| 扫描节点 | `NodesPage`（经 NodeDetailViewModel） |
| 添加节点 | `NodesPage`（经 NodeDetailViewModel） |
| 连接码 | `NodesPage` Dialog |
| 导入/导出 | `SettingsPage`（经 SettingsViewModel） |

**保留的 Store / VM / Controller**：

| 层 | 内容 |
|----|------|
| Store | `FrameStore` / `NodeStore` / `HistoryStore` / `AlertStore` |
| ViewModel | `DashboardViewModel` / `NodeDetailViewModel` / `SettingsViewModel`（monitor/alert 经页面内 VM） |
| Controller | `NavigationController` / `DataController` / `AlertController` / `WindowController` |

## 二、本次改动文件

| 文件 | 改动 |
|------|------|
| `host/gui/controllers/data_controller.py` | **修改**：`add_node` 内静态 `from host.connection import NodeConnection` 改为经 `host.facade.connection_factory.create_connection` 工厂创建，消除 UI 层对 Connection 的静态依赖 |
| `host/facade/connection_factory.py` | **新增**：连接工厂（惰性导入 `NodeConnection`），作为 host/gui ↔ Connection 的唯一桥梁 |
| `host/facade/__init__.py` | **修改**：导出 `create_connection` |
| `host/manager/tray_manager.py` | **修改**：新增 `_is_headless()` 预检，offscreen/minimal/无显示服务器环境直接降级禁用托盘，避免 `QSystemTrayIcon.isSystemTrayAvailable()` 在 headless 环境原生段错误 |

> 注：Phase 3-8 的 legacy UI 删除（`_build_ui` / 顶部工具栏 / overview_grid）已在上一会话完成；本会话聚焦**架构约束修复**与**全量回归验证**。

## 三、引用变化

### NodeConnection 引用

| 原 | 新 |
|----|----|
| `host/gui/controllers/data_controller.py` 内 `from host.connection import NodeConnection` | `from host.facade.connection_factory import create_connection` |
| — | `host/facade/connection_factory.py` 内惰性 `from host.connection import NodeConnection`（唯一静态引用点） |

### TrayManager headless 降级

| 原 | 新 |
|----|----|
| 仅 `_HAS_TRAY` 检查（PyQt5 缺失时） | 追加 `_is_headless()`：`QT_QPA_PLATFORM` ∈ {offscreen, minimal, minimalegl, headless, vnc}，或 Linux 无 `DISPLAY`/`WAYLAND_DISPLAY` 时直接降级 |

## 四、测试结果（全量回归）

| 测试 | 结果 | 说明 |
|------|------|------|
| test_api.py | **14/14** | Agent REST + WS 端到端 |
| test_p0.py | **45/45** | P0 功能 |
| test_v52_phase0.py | **83/83** | Store / facade / service / manager |
| test_v52_phase2.py | **24/24** | 解耦 |
| test_v52_phase28.py | **27/27** | 数据源收敛 |
| test_v52_alert_vm.py | **31/31** | AlertViewModel |
| test_v52_alerts_page.py | **30/30** | AlertsPage |
| test_v52_chart_widget.py | **14/14** | ChartWidget |
| test_v52_dashboard_page.py | **24/24** | DashboardPage |
| test_v52_dashboard_vm.py | **35/35** | DashboardViewModel |
| test_v52_detail_panel.py | **48/48** | DetailPanel（shim 兼容） |
| test_v52_main_window.py | **19/19** | MainWindow 精简架构（本 Phase 核心测试） |
| test_v52_monitor_page.py | **21/21** | MonitorPage |
| test_v52_monitor_vm.py | **46/46** | MonitorViewModel |
| test_v52_node_detail_vm.py | **89/89** | NodeDetailViewModel |
| test_v52_node_widgets.py | **35/35** | NodeCard / NodeListWidget 等 |
| test_v52_nodes_page.py | **10/10** | NodesPage |
| test_v52_settings_vm.py | **30/30** | SettingsViewModel |
| test_v52_ui_polish.py | **40/40** | UI 升级 + 架构扫描 |
| **合计** | **665 通过，0 失败** | 含 PyQt5 GUI 测试（offscreen 平台） |

**关键架构扫描**（test_v52_main_window.py）：
- ✅ `MainWindow` 行数 < 450（实际 311）
- ✅ 无 `_build_ui` / `overview_grid` / `OverviewGrid(` / `common.gui.detail_panel` / `NodeListWidget(` 直接构造
- ✅ 无 `QSystemTrayIcon(` / `_alert_state`
- ✅ 有 Controllers + 5 页面 + property 代理

**关键架构扫描**（test_v52_ui_polish.py §8）：
- ✅ `host/gui` 下（除 main_window）无 `FrameStore` / `NodeStore` / `NodeConnection` import

## 五、架构约束

- ✅ **Page 不访问 Store**：5 页面均经 ViewModel / Store 注入
- ✅ **Widget 无业务逻辑**：NodeListWidget / DetailPanel 纯展示
- ✅ **main_window 不含页面 UI 细节**：仅生命周期 + 组装
- ✅ **Controller 不静态依赖 Connection**：经 `connection_factory` 惰性创建

## 六、风险说明

1. **connection_factory 惰性导入**：`NodeConnection` 依赖 PyQt5，factory 内惰性导入不影响无 GUI 环境对 controllers 的测试。
2. **TrayManager headless 预检**：新逻辑在 win32/darwin 直接跳过（这两类平台默认有托盘）；Linux 需 `DISPLAY`/`WAYLAND_DISPLAY`。真机行为应与 v5.1 一致（有显示环境仍走 `isSystemTrayAvailable()`）。
3. **LOCAL_NODE_ID 仍有三处定义**：`host/local_node.py`、`host/gui/widgets/node_list.py`、`host/gui/controllers/data_controller.py`。本次未统一（避免扩大改动面），建议后续 Phase 3-10 收敛到 common。
4. **common/gui/detail_panel.py shim**：agent 仪表盘仍依赖，保留转发；Phase 3-10 计划删除。
5. **ChartWidget 惰性导入**：依赖 pyqtgraph，缺失时 `ChartWidget = None`，不破坏 widgets 包。
6. **沙箱验证**：PyQt5 GUI 测试在沙箱经 `QT_QPA_PLATFORM=offscreen` 通过；真实渲染建议真机确认。

---

**结论**：Phase 3-8 完成。`main_window.py` 收敛至 311 行纯生命周期层，legacy UI 全部移除，5 页面经 VM 注入，Controllers 承担业务编排，全量 665 项测试通过。架构链已就绪：`main.py → MainWindow → {Page → ViewModel} → Store`。
