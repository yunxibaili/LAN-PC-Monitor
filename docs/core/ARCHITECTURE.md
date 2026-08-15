# 当前最终架构

> **Version**: v5.2.3
> **Status**: STABLE

## 1. 总体架构

```
Agent (采集+推送)
  ↓ WebSocket (每秒)
Connection (WS 客户端, Signal 驱动)
  ↓
Store (FrameStore / NodeStore / HistoryStore / AlertStore)
  ↓
ViewModel (数据转换层, 不含 PyQt5)
  ↓
Page (页面容器, 只导入 Widget + ViewModel)
  ↓
Widget (UI 组件, 只导入 Theme)
  ↓
Theme (ThemeColors / ThemeSpacing / ThemeTypography)
```

## 2. Host 目录结构

```
host/
 ├── config.py                # host_config.json 读写
 ├── connection.py            # NodeConnection (WebSocket 客户端)
 ├── discovery.py             # UDP/mDNS 监听
 ├── local_node.py            # 本机节点
 ├── alerts.py                # 红线告警引擎
 ├── connection_core.py       # ConnectionCore（纯 Python，无 PyQt5）
 ├── self_monitor.py          # 自监控（转发 common.self_monitor）
 ├── facade/
 │   ├── settings_facade.py   # Settings 门面
 │   ├── history_facade.py    # History 读取门面 (5-3)
 │   ├── alert_adapter.py     # 告警适配器
 │   └── connection_factory.py# 连接工厂（惰性导入）
 ├── store/
 │   ├── signals.py           # Signal 信号
 │   ├── frame_store.py       # 帧数据存储
 │   ├── node_store.py        # 节点状态存储
 │   ├── history_store.py     # 历史数据存储
 │   └── alert_store.py       # 告警存储
 ├── service/
 │   ├── alert_service.py     # 告警服务
 │   ├── discovery_service.py # 发现服务
 │   ├── metric_persistence.py # Runtime Frame → Storage Record (5-2)
 │   └── storage_service.py   # Storage 组装 + 生命周期 (5-5B)
 ├── storage/                 # SQLite 持久化 (5-1)
 │   ├── database.py          # SQLite connection + lifecycle
 │   ├── schema.py            # 表定义 + 版本管理
 │   ├── records.py           # MetricRecord / AlertHistoryRecord / SessionRecord
 │   ├── retention.py         # RetentionPolicy + RetentionService (5-5A)
 │   └── repositories/
 │       ├── metrics_repo.py
 │       ├── alerts_repo.py
 │       └── sessions_repo.py
 ├── viewmodels/
 │   ├── dashboard_vm.py      # Dashboard 数据转换
 │   ├── node_detail_vm.py    # 节点详情数据转换
 │   ├── monitor_vm.py        # Monitor 数据转换
 │   ├── alert_vm.py          # Alert 数据转换
 │   ├── history_vm.py        # History 趋势数据 (5-4)
 │   └── settings_vm.py       # Settings 数据转换
 ├── manager/
 │   └── tray_manager.py      # 托盘管理
 └── gui/
     ├── main_window.py       # 主窗口
     ├── discovery_dialog.py  # 节点添加对话框
     ├── controllers/
     │   ├── navigation_controller.py
     │   ├── data_controller.py
     │   ├── alert_controller.py
     │   └── window_controller.py
     ├── navigation/
     │   └── side_nav.py
     ├── theme/               # 设计系统
     │   ├── colors.py        # ThemeColors
     │   ├── spacing.py       # ThemeSpacing
     │   ├── typography.py    # ThemeTypography
     │   ├── metrics.py       # ThemeMetrics
     │   ├── style.py         # QSS 样式
     │   ├── components.py
     │   ├── layout.py
     │   ├── icons.py
     │   └── animation.py
     ├── pages/
     │   ├── base_page.py     # 页面基类
     │   ├── dashboard_page.py
     │   ├── nodes_page.py
     │   ├── monitor_page.py
     │   ├── alerts_page.py
     │   ├── history_page.py  # 历史趋势 (5-4)
     │   └── settings_page.py
     └── widgets/             # UI 组件（20 个 + archive/ 4 个）
         ├── node_card.py     # 节点概览卡（Dashboard）
         ├── resource_card.py # 资源圆环卡（DetailDashboard）
         ├── chart_widget.py  # 折线图
         ├── chart_panel.py   # 图表面板（MonitorPage）+ SummaryCard（Dashboard/History）
         ├── node_explorer.py # 节点探索面板（NodesPage）
         ├── detail_dashboard.py # 节点详情仪表盘（NodesPage）
         ├── monitor_header.py   # 监控页头部（MonitorPage）
         ├── metric_selector.py  # 指标选择器（MonitorPage）
         ├── header_bar.py    # 顶部导航栏（MainWindow）
         ├── detail_panel.py  # 节点详情面板（NodeDetailData + host.gui.theme）
         ├── node_list.py     # NodeListWidget（旧版列表组件）
         ├── alert_card.py    # 告警卡片（AlertsPage）
         ├── alert_summary_card.py # 告警汇总卡（AlertsPage）
         ├── alert_toolbar.py # 告警工具栏（AlertsPage）
         ├── alert_detail.py  # 告警详情面板（AlertsPage）
         ├── status_badge.py  # 状态徽章（测试引用）
         ├── quality_badge.py # 网络质量徽章（测试引用）
         ├── empty_state.py   # 空状态占位（测试引用）
         ├── page_header.py   # 页面头部（测试引用）
         ├── metric_bar.py    # 进度条（测试引用）
         └── archive/         # 归档（app_card/card_widget/metric_card/section_title）
```

## 3. 模块职责

### Store 层

| Store | 职责 | 信号 |
|-------|------|------|
| FrameStore | 缓存每节点最新帧 | frame_updated |
| NodeStore | 节点元数据/状态/RTT | node_added/removed |
| HistoryStore | 历史趋势数据 (maxlen=300) | point_added |
| AlertStore | 告警记录 (30s去重) | alert_added |

### ViewModel 层

| VM | 输入 | 输出 | 信号 |
|----|------|------|------|
| DashboardViewModel | NodeStore + FrameStore | 节点卡片数据 | data_changed |
| NodeDetailViewModel | NodeStore + FrameStore | 节点详情数据 | data_changed |
| MonitorViewModel | HistoryStore + NodeStore | 图表数据点 | data_changed |
| AlertViewModel | AlertStore | 告警列表 | alerts_changed |
| HistoryViewModel | HistoryFacade | 历史趋势数据 | data_changed |
| SettingsViewModel | SettingsFacade | 配置数据 | settings_changed |

### Page 层

| Page | 布局 | 依赖 |
|------|------|------|
| DashboardPage | SummaryCards + NodeGrid | DashboardVM |
| NodesPage | NodeExplorer + DetailDashboard | NodeDetailVM |
| MonitorPage | MonitorHeader + MetricSelector + ChartPanel | MonitorVM |
| AlertsPage | SummaryCards + AlertTable | AlertVM |
| HistoryPage | 指标选择 + ChartPanel + SummaryCard | HistoryVM |
| SettingsPage | 5-Tab 设置 | SettingsVM |

## 4. 依赖规则

### ✅ 允许

```
Page → Widget (UI 组件)
Page → ViewModel (数据转换)
Widget → Theme (样式常量)
ViewModel → Store (数据存储)
```

### ❌ 禁止

```
Page → Store ❌
Page → Connection ❌
Page → ConfigManager ❌
Widget → Store ❌
Widget → ViewModel ❌
ViewModel → PyQt5 ❌
```

## 5. MainWindow 职责

`main_window.py` (326行) 只负责：

| ✅ 允许 | ❌ 禁止 |
|---------|---------|
| 创建 Store / Service / Facade | 创建 Card / Button |
| 创建 ViewModel | 创建 Table |
| 注册 6 个页面 | 数据转换 |
| 创建 Controllers | 业务逻辑 |
| 连接 Signal | UI 渲染 |

## 6. Signal 驱动

所有数据更新由 Qt Signal 驱动，**不使用 QTimer 轮询**：

```
NodeConnection.data_received → DataController → Store.push
  → Store.frame_updated → VM.data_changed → Page._refresh
```

## 6.1 持久化数据流（Phase 5）

```
Collector (Agent 帧)
  ↓
DataController._on_data() → MetricPersistenceService.write_frame()
  ↓
StorageService (Database + Repositories + RetentionService)
  ├── MetricsRepository    → metrics 表
  ├── AlertsRepository     → alert_history 表
  └── SessionsRepository   → sessions 表
  ↓
HistoryFacade (查询边界：range / latest / aggregate)
  ↓
HistoryViewModel
  ↓
HistoryPage (图表)
```

约束：`sqlite3` 只在 `host/storage/`；VM 不直接碰 Repository，一律走 Facade；Storage 生命周期由 StorageService 管理（MainWindow 不直接碰 Database）。

## 7. 设计系统

所有 GUI 颜色/间距/字体通过 Theme 引用：

```python
from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.theme.typography import ThemeTypography as TT
```

禁止硬编码颜色/间距。
