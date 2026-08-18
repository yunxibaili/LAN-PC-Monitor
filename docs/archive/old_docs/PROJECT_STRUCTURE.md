# LAN-PC-Monitor 项目结构

> **版本**: v5.3.3
> **架构**: Agent/Host 双角色 + MVVM + SQLite 存储
> **技术栈**: Python 3.10+ / PyQt5 / SQLite / WebSocket / REST

---

## 根目录

```
LAN-PC-Monitor/
├── agent/                    # Agent 端（被监控机，采集+推送）
├── host/                     # Host 端（监控端，接收+展示）
├── common/                   # 共享模块（采集器/工具/UI 组件）
├── tests/                    # 测试（自定义 check runner，989/989 PASS）
├── docs/                     # 文档（架构/路线图/审计报告/Release Notes）
├── i18n/                     # 国际化（中英双语）
├── tools/                    # 工具脚本
├── logs/                     # 运行日志（gitignore）
├── build/                    # PyInstaller 构建产物（gitignore）
├── dist/                     # 分发包（gitignore）
│
├── requirements.txt          # 完整依赖（含注释，开发用）
├── requirements-common.txt   # 共用依赖（Agent + Host）
├── requirements-agent.txt    # Agent 专属依赖
├── requirements-host.txt     # Host 专属依赖
│
├── agent_config.json         # Agent 运行时配置（gitignore）
├── host_config.json          # Host 运行时配置（gitignore）
├── start_agent.bat           # 一键启动 Agent
├── start_host.bat            # 一键启动 Host
│
├── CHANGELOG.md              # 变更记录
├── CONTRIBUTING.md           # 贡献指南
├── README.md                 # 项目说明
├── .gitignore
└── .github/
    ├── workflows/
    │   └── windows-tests.yml # CI: Windows Python 3.10/3.11 矩阵
    └── ISSUE_TEMPLATE/
        ├── bug_report.yml
        ├── feature_request.yml
        └── config.yml
```

---

## agent/ — 被监控端

```
agent/
├── __init__.py
├── __main__.py              # python -m agent 入口
├── main.py                  # Agent 主循环（采集+推送）
├── config.py                # Agent 配置加载
├── aggregator.py            # 数据聚合（多采集器 → 单帧）
├── http_server.py           # REST API 服务端
├── websocket_server.py      # WebSocket 推送服务端
├── discovery.py             # mDNS + UDP 自动发现
├── local_node.py            # 本机节点信息
├── self_monitor.py          # 自监控（转发 common.self_monitor）
└── gui/
    └── main_window.py       # Agent 本机仪表盘（可选 GUI）
```

**数据流**: Collector → Aggregator → WebSocket 推送 + HTTP API

---

## host/ — 监控端

```
host/
├── __init__.py
├── __main__.py              # python -m host 入口
├── main.py                  # Host 启动器
├── config.py                # Host 配置加载
├── connection.py            # WS 客户端（Qt 线程适配）
├── connection_core.py       # WS 客户端（纯 Python，无 Qt 依赖）
├── discovery.py             # 节点发现
├── alerts.py                # 告警引擎（红线检测）
├── local_node.py            # 本机节点
├── self_monitor.py          # 自监控
│
├── store/                   # 运行时数据存储（纯 Python 信号）
│   ├── signals.py           # Signal 实现（非 pyqtSignal）
│   ├── frame_store.py       # 实时帧缓存（最新帧/历史帧）
│   ├── node_store.py        # 节点状态管理
│   ├── history_store.py     # 历史帧内存缓存
│   └── alert_store.py       # 告警状态管理
│
├── viewmodels/              # ViewModel（纯 Python，不依赖 PyQt5）
│   ├── dashboard_vm.py      # Dashboard 数据转换
│   ├── node_detail_vm.py    # 节点详情数据转换
│   ├── monitor_vm.py        # Monitor 数据转换
│   ├── alert_vm.py          # Alert 数据转换
│   ├── history_vm.py        # History 查询 + 聚合
│   └── settings_vm.py       # Settings 数据转换
│
├── facade/                  # 门面层（隔离 VM 与 Service/Storage）
│   ├── settings_facade.py   # 配置读写门面
│   ├── history_facade.py    # 历史查询门面
│   ├── alert_adapter.py     # 告警适配器
│   └── connection_factory.py # 连接工厂（惰性导入 Qt）
│
├── service/                 # 业务服务层
│   ├── alert_service.py     # 告警服务
│   ├── discovery_service.py # 发现服务
│   ├── storage_service.py   # 存储组装 + 生命周期
│   └── metric_persistence.py # 指标持久化（Frame → Record）
│
├── storage/                 # SQLite 持久化层
│   ├── database.py          # 连接管理 + Schema 初始化
│   ├── schema.py            # 表定义 + 版本管理
│   ├── records.py           # MetricRecord / AlertHistoryRecord / SessionRecord
│   ├── retention.py         # 数据保留策略 + 清理
│   └── repositories/
│       ├── metrics_repo.py  # 指标查询（range / latest / aggregate）
│       ├── alerts_repo.py   # 告警历史查询
│       └── sessions_repo.py # 会话查询
│
├── manager/
│   └── tray_manager.py      # 系统托盘管理
│
└── gui/                     # PyQt5 UI 层
    ├── main_window.py       # 主窗口（组装所有组件）
    ├── discovery_dialog.py  # 节点添加对话框
    │
    ├── controllers/         # 控制器（协调 Store ↔ VM ↔ Page）
    │   ├── navigation_controller.py
    │   ├── data_controller.py      # WS 数据入口 + 持久化
    │   ├── alert_controller.py     # 告警触发 + 通知
    │   └── window_controller.py    # 窗口事件处理
    │
    ├── pages/               # 页面（每个 Page = 独立功能区）
    │   ├── base_page.py     # PageBase 抽象基类
    │   ├── dashboard_page.py    # 总览（System Overview + Node Grid）
    │   ├── nodes_page.py        # 节点管理
    │   ├── monitor_page.py      # 单节点深度监控
    │   ├── alerts_page.py       # 告警列表
    │   ├── history_page.py      # 历史趋势（多曲线 + 时间选择）
    │   └── settings_page.py     # 设置
    │
    ├── widgets/             # 可复用 UI 组件
    │   ├── chart_widget.py      # 折线图（pyqtgraph，支持多曲线 + tooltip）
    │   ├── chart_panel.py       # 图表面板（Chart + SummaryCards）
    │   ├── metric_bar.py        # 指标进度条（标签 + 数值 + bar）
    │   ├── node_card.py         # 节点概览卡片
    │   ├── header_bar.py        # 顶部导航栏
    │   ├── page_header.py       # 页面标题栏
    │   ├── status_badge.py      # 状态标签
    │   ├── quality_badge.py     # 网络质量标签
    │   ├── resource_card.py     # 资源卡片
    │   ├── alert_card.py        # 告警卡片
    │   ├── alert_summary_card.py # 告警摘要卡片
    │   ├── alert_detail.py      # 告警详情
    │   ├── alert_toolbar.py     # 告警工具栏
    │   ├── detail_panel.py      # 详情面板（Agent/Host 分版）
    │   ├── detail_dashboard.py  # 详情仪表盘
    │   ├── node_explorer.py     # 节点浏览器
    │   ├── node_list.py         # 节点列表
    │   ├── metric_selector.py   # 指标选择器
    │   ├── monitor_header.py    # 监控页标题
    │   ├── empty_state.py       # 空状态占位
    │   └── archive/             # 归档组件（保留，不使用）
    │
    ├── navigation/
    │   └── side_nav.py      # 侧边导航栏
    │
    └── theme/               # 设计系统
        ├── colors.py        # 颜色 token（来自 theme_tokens + 语义色）
        ├── spacing.py       # 间距常量
        ├── typography.py    # 字体常量
        ├── metrics.py       # 尺寸常量
        ├── style.py         # 通用样式
        ├── components.py    # 组件样式预设
        ├── formatters.py    # 数值格式化
        ├── icons.py         # 图标常量
        ├── animation.py     # 动画常量
        └── layout.py        # 布局常量
```

### 数据流（完整链路）

```
Agent Collector
    ↓ WebSocket
Host DataController
    ├── FrameStore (实时帧)
    ├── NodeStore (节点状态)
    ├── HistoryStore (内存历史)
    ├── AlertStore (告警状态)
    ├── AlertService (红线检测 → 告警)
    └── MetricPersistenceService → StorageService → SQLite
                                        ↓
                              HistoryFacade → HistoryVM → HistoryPage
                              RetentionService (定期清理)
```

### 分层约束

```
GUI (Page/Widget) ←→ ViewModel ←→ Facade ←→ Service/Repository ←→ SQLite
      ↓                  ↓
   只看 Theme         只看 Signal（非 pyqtSignal）
   不碰 Store         不碰 PyQt5 / sqlite3
```

| 规则 | 说明 |
|------|------|
| Page → Store/Config/Storage | ❌ 禁止跳层 |
| VM → PyQt5 / sqlite3 | ❌ VM 必须纯 Python |
| sqlite3 → storage/ 外 | ❌ 仅 host/storage/ 可用 |
| 硬编码颜色 | ❌ 必须走 Theme tokens |

---

## common/ — 共享模块

```
common/
├── collectors/              # 硬件采集器（Agent + Host 共用）
│   ├── base.py              # CollectorBase 抽象基类
│   ├── cpu_collector.py     # CPU（py-cpuinfo）
│   ├── gpu_collector.py     # GPU（nvidia-ml-py / pyadl）
│   ├── ram_collector.py     # 内存
│   ├── disk_collector.py    # 磁盘
│   ├── net_collector.py     # 网络流量
│   ├── net_quality_collector.py # 网络质量（ping 网关）
│   ├── fps_collector.py     # 帧率（DXCAM / dxcam）
│   ├── proc_collector.py    # 进程
│   └── sys_collector.py     # 系统信息（hostname / IP / uptime）
│
├── gui/                     # Agent/Host 共享 GUI 组件
│   └── detail_panel.py      # 详情面板（Agent/Host 各自分版）
│
├── utils.py                 # 通用工具（IP 选取 / 网关 / host_id）
├── theme_tokens.py          # 颜色 token 单一来源（host + agent 共用）
├── theme.py                 # Agent 用主题（Legacy，Phase 4-7 迁移）
├── config_manager.py        # 配置管理器
├── quality.py               # 网络质量评分算法
├── i18n.py                  # 国际化
├── constants.py             # 全局常量
├── connect_code.py          # 连接码生成/校验
├── connect_dialog.py        # 连接对话框
├── logger.py                # 日志配置
├── protocol.py              # v4 TCP 遗留（待归档）
├── self_monitor.py          # 自监控基础
├── single_instance.py       # 单实例检查
├── startup.py               # 开机启动
├── settings_dialog.py       # 设置对话框
└── lhm.py                   # 本地硬件监控辅助
```

---

## tests/ — 测试体系

```
tests/
├── test_api.py                      # REST + WebSocket 端到端（14/14）
├── test_p0.py                       # 协议/采集器/配置（45/45）
├── test_metric_persistence.py       # 存储管线单元测试（22/22）
├── test_metric_persistence_flow.py  # 数据流集成测试（5/5）
│
├── test_v52_dashboard_page.py       # Dashboard 组装（24/24）
├── test_v52_dashboard_vm.py         # Dashboard VM
├── test_v52_dashboard_polish.py     # Dashboard 增强
├── test_v52_phase42_dashboard_ui.py # Dashboard UI 适配
│
├── test_v52_history_page.py         # History 页面（21/21）
├── test_v52_history_query.py        # History 查询
│
├── test_v52_alert_vm.py             # Alert VM
├── test_v52_alerts_page.py          # Alerts 页面
├── test_v52_alerts_redesign.py      # Alerts 重设计
│
├── test_v52_monitor_page.py         # Monitor 页面
├── test_v52_monitor_vm.py           # Monitor VM
├── test_v52_monitor_redesign.py     # Monitor 重设计
│
├── test_v52_nodes_page.py           # Nodes 页面
├── test_v52_nodes_redesign.py       # Nodes 重设计
├── test_v52_node_detail_vm.py       # NodeDetail VM
├── test_v52_node_widgets.py         # Node 组件
│
├── test_v52_settings_page.py        # Settings 页面
├── test_v52_settings_vm.py          # Settings VM
├── test_v52_settings_flow.py        # Settings 流程
│
├── test_v52_storage.py              # Storage 层
├── test_v52_storage_service.py      # StorageService
├── test_v52_retention.py            # 数据保留
│
├── test_v52_theme_tokens.py         # Theme Token 一致性
├── test_v52_ui_design_system.py     # UI 设计规范
├── test_v52_ui_polish.py            # UI 打磨
├── test_v52_app_shell.py            # App Shell
├── test_v52_main_window.py          # MainWindow
├── test_v52_chart_widget.py         # ChartWidget
├── test_v52_detail_panel.py         # DetailPanel
│
├── test_v52_phase28.py              # Phase 2.8 测试
├── test_v52_phase0.py               # Phase 0 测试（本机崩溃，环境问题）
├── test_v52_phase2.py               # Phase 2 测试（本机崩溃，环境问题）
└── test_p4.py                       # P4 测试（废弃 shim）
```

**运行方式**: `python logs/run_all_tests_v3.py`（自定义 check runner，非 pytest）

---

## docs/ — 文档

```
docs/
├── README.md                       # 文档入口
├── core/                           # 核心文档
│   ├── BLUEPRINT.md                # 项目总蓝图（唯一入口）
│   ├── ARCHITECTURE.md             # 最终架构
│   ├── UI_SYSTEM.md                # UI 设计规范
│   ├── DATA_FLOW.md                # 数据流
│   ├── DEVELOPMENT.md              # 开发规范
│   └── ROADMAP.md                  # 路线图
├── releases/                       # Release Notes
│   ├── v5.2.3.md                   # v5.2.3 发布说明
│   └── v5.2.x_freeze.md           # 冻结策略
├── issues/
│   └── v5.2.3_known_issues.md      # 已知问题登记
├── phases/                         # Phase 执行计划
│   └── phase_5_3_1_runtime_reliability_plan.md
├── plans/                          # 规划文档
│   └── project_cleanup_plan.md
├── reports/                        # 审计/清理报告
│   ├── v5.2.3_release_audit.md     # 发布审计
│   ├── baseline_v5.2.3.txt         # 测试基线
│   ├── project_full_audit_report.md # 全量审计
│   └── ...
├── archive/                        # 历史归档
└── ui_mockup*.html                 # UI 原型
```

---

## i18n/ — 国际化

```
i18n/
├── zh_CN.json              # 中文
└── en_US.json              # 英文
```

---

## 架构层级图

```
┌─────────────────────────────────────────────────────────────┐
│                       GUI Layer                             │
│  Page → Widget → Theme tokens                               │
│  (Page 不碰 Store / Config / Storage / sqlite3)             │
├─────────────────────────────────────────────────────────────┤
│                    ViewModel Layer                           │
│  DashboardVM / HistoryVM / AlertVM / SettingsVM             │
│  (纯 Python，不碰 PyQt5 / sqlite3)                          │
├─────────────────────────────────────────────────────────────┤
│                     Facade Layer                             │
│  SettingsFacade / HistoryFacade / AlertAdapter              │
│  (隔离 VM 与 Service / Storage)                              │
├─────────────────────────────────────────────────────────────┤
│                    Service Layer                             │
│  AlertService / DiscoveryService / StorageService            │
│  MetricPersistenceService                                   │
├─────────────────────────────────────────────────────────────┤
│                   Storage Layer                              │
│  Database → Schema → Repository → SQLite                    │
│  (sqlite3 仅限 host/storage/)                               │
├─────────────────────────────────────────────────────────────┤
│                    Store Layer                               │
│  FrameStore / NodeStore / HistoryStore / AlertStore         │
│  (纯 Python Signal，非 pyqtSignal)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 技术栈

| 层 | 技术 |
|----|------|
| GUI | PyQt5 5.15+ |
| Charts | pyqtgraph（惰性导入 + fallback） |
| Storage | SQLite 3（WAL 模式） |
| 通信 | WebSocket + HTTP REST |
| 采集 | psutil / py-cpuinfo / nvidia-ml-py / dxcam |
| 发现 | zeroconf (mDNS) + UDP 广播 |
| 测试 | 自定义 check runner（非 pytest） |
| 构建 | PyInstaller |
| CI | GitHub Actions (Windows 3.10/3.11) |
