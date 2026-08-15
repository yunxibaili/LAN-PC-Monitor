# Project Blueprint

> **Version**: v5.2.3
> **Generated**: 2026-08-21
> **Status**: Stable — v5.2.3 Stable Release（Architecture Stabilization）
> **Intended audience**: Developers, AI assistants, future maintainers

---

## 1. 项目定位

**PC Monitor** 是一套**局域网远程电脑监控系统**，用于实时监控多台 Windows 电脑的硬件状态。

### 解决的问题

- 多台电脑硬件状态需要逐台查看 → **集中大屏**
- 异常指标无感知 → **红线告警 + 托盘通知**
- 手动配置复杂 → **零配置自动发现**

### 使用场景

- 游戏工作室监控多台游戏主机
- 开发团队监控渲染节点
- 个人多设备管理

### 当前版本定位

v5.2 是**架构重构 + UI 升级版本**，从 v5.0 的纯文字面板升级为 SaaS 风格深色主题桌面监控大屏。

---

## 2. 当前状态

| 维度 | 状态 |
|------|------|
| Version | v5.2.3 |
| Git Tag | v5.2.3 |
| Architecture | ✅ MVVM 完整 |
| Design System | ✅ ThemeColors/Spacing/Typography |
| Dashboard | ✅ 完整 |
| Nodes | ✅ 完整 |
| Monitor | ✅ 完整 |
| Alerts | ✅ Phase 4-5 重构完成 |
| Settings | ✅ Phase 4-6 重构完成 |
| History | ✅ Phase 5-4 重构完成 |
| Storage | ✅ Phase 5-1 ~ 5-5 完整 |
| Documentation | ✅ core/ 8 篇权威文档 |
| Tests | ✅ 全量回归 PASS（988/988，见 §10） |

### 已完成

| Phase | 内容 |
|-------|------|
| Phase 3-3~3-9 | MVVM 架构迁移 |
| Phase 4-1 | Design System (ThemeColors/Spacing/Typography) |
| Phase 4-2 | App Shell (HeaderBar + SideNav) |
| Phase 4-3 | NodesPage Redesign |
| Phase 4-4 | MonitorPage Redesign |
| Phase 4-5 | AlertsPage Redesign + Final Polish |
| Phase 4-6 | SettingsPage Redesign (A/B/C) |
| Phase RC-1~6 | 文档整理 + 代码清理 + 基线冻结 |
| RC-7 | Theme Token Consolidation |
| Phase 5-1 | Storage Foundation |
| Phase 5-2 | Metrics Persistence |
| Phase 5-3 | History Query API |
| Phase 5-4 | History UI |
| Phase 5-5 | Retention (5-5A Foundation + 5-5B Startup Trigger) |

### 进行中

| Phase | 内容 |
|-------|------|
| （无） | — |

### 未来（未实现）

| Phase | 内容 | 标记 |
|-------|------|------|
| Phase 4-7 | Agent GUI 升级 | Future |
| Phase 5-5C | Retention Settings Integration | Future |
| Phase 6 | 高级告警引擎 | Future |
| Phase 7 | UX 优化 | Future |
| Phase 8+ | 服务化架构 | Future |

---

## 3. 技术栈

### Host（监控大屏）

| 层 | 技术 | 说明 |
|----|------|------|
| Language | Python 3.10+ | |
| GUI | PyQt5 | QFrame/QVBoxLayout/Signal-Slot |
| Charts | pyqtgraph | 实时折线图（可选，无则 fallback） |
| Drawing | QPainter | 环形进度/径向仪表 |
| Config | JSON | agent_config.json / host_config.json |

### Agent（采集服务）

| 层 | 技术 | 说明 |
|----|------|------|
| Language | Python 3.10+ | |
| HTTP | aiohttp | REST API |
| WebSocket | aiohttp | 实时推送 |
| Discovery | UDP broadcast + mDNS | zeroconf |

### 公共层

| 模块 | 说明 |
|------|------|
| common/collectors | 硬件采集器（CPU/GPU/RAM/Disk/Net/FPS/Process） |
| common/config_manager | 配置读写（JSON） |
| common/quality | 网络质量评分 |
| common/theme | Agent 侧基础主题（兼容层） |
| common/i18n | 国际化 |

### 存储层

| 技术 | 用途 | 说明 |
|------|------|------|
| SQLite | 指标/告警/会话持久化 | Phase 5-1 引入，位于 host/storage/ |

### 未来技术（未引入）

| 技术 | 用途 | 状态 |
|------|------|------|
| PySide6 / Qt6 | GUI 迁移 | Future |
| Electron | 跨平台 UI | Future |

---

## 4. 系统架构

```
Agent (每台被监控电脑)
 │
 │  Collector (线程池, 每秒采集)
 │    ↓ get()
 │  Aggregator (组装 monitor_data 帧)
 │    ↓ 最新帧缓存
 │  WebSocket Server (广播给所有订阅者)
 │  HTTP Server (REST API)
 │  UDP Broadcaster (自动发现心跳)
 │
 ↓ WebSocket (ws://ip:12345/ws?token=xxx)
 │
Host (监控大屏)
 │
 │  NodeConnection (WS 客户端, Signal 驱动)
 │    ↓ data_received.emit(frame, node_id)
 │  DataController (主线程 slot)
 │    ↓
 │  ├── FrameStore (最新帧缓存)
 │  ├── HistoryStore (历史趋势, maxlen=300)
 │  ├── NodeStore (节点状态)
 │  ├── AlertStore (告警记录, 30s 去重)
 │  └── AlertService (红线检测)
 │    ↓
 │  ViewModel (数据转换, 不含 PyQt5)
 │    ↓
 │  Page (页面容器, 只导入 Widget + ViewModel)
 │    ↓
 │  Widget (UI 组件, 只导入 Theme)
 │    ↓
 │  Theme (ThemeColors / ThemeSpacing / ThemeTypography)
```

### 依赖规则

| ✅ 允许 | ❌ 禁止 |
|---------|---------|
| Page → Widget | Page → Store |
| Page → ViewModel | Page → Connection |
| Widget → Theme | Widget → Store / ViewModel |
| ViewModel → Store | ViewModel → PyQt5 |
| Facade → ConfigManager | Page → ConfigManager |

---

## 5. Host 架构

### 目录结构

```
host/
 ├── main.py                 # 入口 (67 行)
 ├── config.py               # host_config.json 读写
 ├── connection.py           # NodeConnection (Qt Signal 适配)
 ├── connection_core.py      # ConnectionCore (纯 Python WS 客户端)
 ├── discovery.py            # UDP/mDNS 监听
 ├── local_node.py           # 本机节点采集
 ├── alerts.py               # 红线告警引擎
 ├── self_monitor.py         # 转发 common.self_monitor
 │
 ├── facade/
 │   ├── settings_facade.py  # Settings 门面
 │   ├── history_facade.py   # History 读取门面 (5-3)
 │   ├── alert_adapter.py    # AlertEngine → AlertStore 适配
 │   └── connection_factory.py # NodeConnection 惰性工厂
 │
 ├── store/
 │   ├── frame_store.py      # 每节点最新帧
 │   ├── node_store.py       # 节点元数据/状态/RTT
 │   ├── history_store.py    # 历史趋势 (deque maxlen=300)
 │   ├── alert_store.py      # 告警记录 (30s 去重)
 │   └── signals.py          # 统一 Signal 定义
 │
 ├── service/
 │   ├── alert_service.py    # AlertEngine + AlertStore 管线
 │   ├── discovery_service.py # UDP + mDNS 服务封装
 │   ├── metric_persistence.py # Runtime Frame → Storage Record (Phase 5-2)
 │   └── storage_service.py  # Storage 组装 + 生命周期 (5-5B)
 │
 ├── storage/               # SQLite 持久化 (Phase 5-1)
 │   ├── database.py         # SQLite connection + lifecycle
 │   ├── schema.py           # 表定义 + 版本管理
 │   ├── records.py          # MetricRecord / AlertHistoryRecord / SessionRecord
 │   ├── retention.py        # RetentionPolicy + RetentionService (5-5A)
 │   └── repositories/
 │       ├── metrics_repo.py
 │       ├── alerts_repo.py
 │       └── sessions_repo.py
 │
 ├── viewmodels/
 │   ├── dashboard_vm.py     # Dashboard 数据转换
 │   ├── node_detail_vm.py   # 节点详情数据转换
 │   ├── monitor_vm.py       # Monitor 图表数据
 │   ├── alert_vm.py         # Alert 列表转换
 │   ├── history_vm.py       # History 趋势数据 (5-4)
 │   └── settings_vm.py      # Settings 桥接
 │
 ├── manager/
 │   └── tray_manager.py     # 系统托盘
 │
 └── gui/
     ├── main_window.py      # 主窗口 (326 行)
     ├── discovery_dialog.py # 自动发现弹窗
     ├── controllers/
     │   ├── navigation_controller.py
     │   ├── data_controller.py
     │   ├── alert_controller.py
     │   └── window_controller.py
     ├── navigation/
     │   └── side_nav.py
     ├── theme/              # 设计系统 (10 文件)
     │   ├── colors.py       # ThemeColors
     │   ├── spacing.py      # ThemeSpacing
     │   ├── typography.py   # ThemeTypography
     │   ├── formatters.py   # 统一格式化函数
     │   ├── components.py   # 组件样式 + remove_help_button
     │   ├── style.py        # dark_qss
     │   ├── metrics.py / layout.py / icons.py / animation.py
      ├── pages/              # 6 页面 + base_page
      │   ├── dashboard_page.py
      │   ├── nodes_page.py
      │   ├── monitor_page.py
      │   ├── alerts_page.py
      │   ├── history_page.py # 历史趋势 (5-4)
      │   └── settings_page.py
     └── widgets/            # 20 活跃 + 4 归档
         ├── [Dashboard] node_card.py, resource_card.py
         ├── [Nodes] node_explorer.py, detail_dashboard.py, detail_panel.py, node_list.py
         ├── [Monitor] chart_widget.py, chart_panel.py, monitor_header.py, metric_selector.py
         ├── [Alerts] alert_card.py, alert_summary_card.py, alert_toolbar.py, alert_detail.py
         ├── [Shell] header_bar.py
         ├── [保留] status_badge.py, quality_badge.py, empty_state.py, page_header.py, metric_bar.py
         └── [归档] archive/ (app_card, card_widget, metric_card, section_title)
```

### 模块职责

| 层 | 职责 | 关键约束 |
|----|------|----------|
| Page | 布局 + 交互 | 只导入 Widget + ViewModel |
| Widget | 视觉展示 | 只导入 Theme，无业务逻辑 |
| ViewModel | 数据转换 | 不含 PyQt5，从 Store 提取 |
| Store | 数据存储 | Signal 驱动通知 |
| Facade | 业务封装 | 包装 ConfigManager/AlertEngine |
| Controller | 流程编排 | 连接 Signal，不创建 UI |

### MainWindow (242 行)

只负责：
- 创建 Store / Service / Manager
- 创建 ViewModel
- 注册 6 个页面（VM 注入）
- 创建 Controllers
- 连接全局 Signal

禁止：创建 Card / Button / Table / 数据转换

---

## 6. Agent 架构

```
agent/
 ├── main.py                # 入口 (290 行, 含 --gui/--tray 模式)
 ├── config.py              # agent_config.json
 ├── aggregator.py          # 每秒组装 monitor_data 帧
 ├── http_server.py         # REST API (aiohttp)
 ├── websocket_server.py    # WS 推送 (aiohttp)
 ├── discovery.py           # UDP 广播 + mDNS
 ├── local_node.py          # 本机节点采集
 ├── self_monitor.py        # 转发 common.self_monitor
 └── gui/
     └── main_window.py     # 本机仪表盘 (--gui 模式, 可选)
```

### Agent 职责

| 模块 | 职责 |
|------|------|
| aggregator | 每秒从采集器 get() → 组装 monitor_data 帧 → 最新帧缓存 |
| websocket_server | 每秒向所有订阅者广播 monitor_data |
| http_server | REST API (/api/health, /api/nodes, /api/scan, /api/config) |
| discovery | UDP 广播 agent_heartbeat + mDNS 注册 |
| local_node | 本机采集器（可选，--gui 模式用） |

### Agent 与 Host 的关系

- Agent 是 **Server**（HTTP/WS），Host 是 **Client**
- Agent 可被多台 Host 同时订阅
- Agent 之间不直接通信
- 配置文件独立（agent_config.json / host_config.json）

---

## 7. 数据流

### 实时数据路径

```
Agent Collector (每秒)
  ↓ get()
Aggregator → monitor_data 帧
  ↓ WebSocket 广播
Host NodeConnection (WS 线程)
  ↓ data_received.emit(frame, node_id)
DataController._on_data() (主线程)
  ├── FrameStore.push()        → 更新最新帧
  ├── HistoryStore.push()      → 追加历史
  ├── NodeStore.update_status()→ 更新状态
  ├── AlertService._on_frame() → 告警检测
  └── VM.data_changed.emit()   → 通知页面
        ↓
Page._refresh() → Widget.update()
```

### 配置数据路径

```
SettingsPage
  ↓ vm.set(key, value)
SettingsViewModel
  ↓ facade.set(key, value) + facade.save()
SettingsFacade
  ↓ mgr.set_xxx() + mgr.save_all()
ConfigManager
  ↓ _write_json()
agent_config.json / host_config.json
```

### Signal 驱动原则

- 所有数据更新由 Qt Signal 驱动
- **不使用 QTimer 轮询**
- 数据到达即更新，零延迟

---

## 8. UI Design System

### 唯一规范

`docs/core/UI_SYSTEM.md` — 所有 GUI 开发以此为准。

### 核心组件

| 组件 | 用途 | 引用方式 |
|------|------|----------|
| ThemeColors | 颜色常量 | `from host.gui.theme.colors import ThemeColors as TC` |
| ThemeSpacing | 间距常量 | `from host.gui.theme.spacing import ThemeSpacing as S` |
| ThemeTypography | 字体常量 | `from host.gui.theme.typography import ThemeTypography as TT` |
| ThemeComponents | 组件样式 | `from host.gui.theme.components import CardStyle` |
| ThemeFormatters | 数据格式化 | `from host.gui.theme.formatters import format_percent` |

### 强制规则

1. ✅ 颜色引用 `ThemeColors`
2. ✅ 间距引用 `ThemeSpacing`
3. ✅ 字体引用 `ThemeTypography`
4. ❌ 禁止硬编码颜色（host/gui 非 theme 区 0 处）
5. ❌ 禁止内联 QSS hex
6. ❌ 禁止页面私建样式

### Token 定义状态

当前存在三个层级：

**1. Host GUI Theme（当前生产使用）**

```
host/gui/theme/
 ├── colors.py         ThemeColors
 ├── spacing.py        ThemeSpacing
 ├── typography.py     ThemeTypography
 ├── formatters.py     统一格式化
 ├── components.py     组件样式
 ├── style.py          dark_qss
 └── ... (10 files)
```

所有 Host GUI 新开发必须使用此体系。

**2. Common Legacy Theme（历史兼容）**

```
common/theme.py
```

- 保留旧 Agent/公共场景支持
- 不作为 Host GUI 新开发入口
- Agent GUI 仍引用此模块

**3. Common Theme Tokens（RC-7 已接线）**

```
common/theme_tokens.py
```

- 基础设计令牌单一来源
- 被 host/gui/theme 的 colors.py / spacing.py / typography.py 引用
- 无 host 依赖

**当前接线关系**:

```
common/theme_tokens.py (基础 token)
        ↓ import
host/gui/theme/
 ├── colors.py       (基础 token 引用 + 语义 token)
 ├── spacing.py      (引用 theme_tokens)
 └── typography.py   (引用 theme_tokens)
        ↓
Host UI

common/theme.py (legacy, Agent 专用)
        ↓
Agent GUI (Phase 4-7 再迁移)
```

---

## 9. 开发规范

### 禁止事项

| 禁止 | 原因 |
|------|------|
| Page → Store | 违反分层 |
| Page → ConfigManager | 违反分层 |
| Widget → Store / ViewModel | 职责混乱 |
| ViewModel → PyQt5 | 耦合 UI |
| 硬编码颜色 | 破坏主题 |
| QTimer 轮询 | 性能浪费 |
| 直接修改 agent_config.json | 应走 Facade |

### 新增功能流程

```
1. Store      (数据存储, host/store/)
2. ViewModel  (数据转换, host/viewmodels/) — 不含 PyQt5
3. Widget     (UI 组件, host/gui/widgets/) — 只导入 Theme
4. Page       (页面容器, host/gui/pages/) — 只导入 Widget + ViewModel
5. MainWindow (注册页面, VM 注入)
6. Test       (tests/test_v52_xxx.py)
```

### 代码规范

- UTF-8 编码
- 类型注解
- docstring (中文)
- 日志: `logging.getLogger("host.gui.xxx")`
- Signal: `snake_case`
- Slot: `_on_xxx`
- Widget: `PascalCase`

---

## 10. 测试体系

### 运行方式

```bash
# 单个测试
python tests/test_v52_dashboard_vm.py

# 全量 v52 测试
python tests/test_v52_*.py

# 后端测试
python tests/test_api.py    # REST + WebSocket (14 项)
python tests/test_p0.py     # 协议/采集器 (45 项)
```

### 测试框架

- **自定义 check runner**，不使用 pytest
- 每个测试文件独立运行
- 结构：`check(name, cond, detail)` + `main()` 汇总

### 测试结构

```
tests/
 ├── test_api.py              # REST + WebSocket 端到端
 ├── test_p0.py               # 协议/采集器/工具冒烟
 ├── test_v52_dashboard_vm.py # DashboardViewModel
 ├── test_v52_monitor_vm.py   # MonitorViewModel
 ├── test_v52_node_detail_vm.py # NodeDetailViewModel (89 项)
 ├── test_v52_alert_vm.py     # AlertViewModel
 ├── test_v52_settings_vm.py  # SettingsViewModel
 ├── test_v52_dashboard_page.py
 ├── test_v52_nodes_page.py
 ├── test_v52_monitor_page.py
 ├── test_v52_monitor_redesign.py
 ├── test_v52_alerts_page.py
 ├── test_v52_alerts_redesign.py
 ├── test_v52_detail_panel.py
 ├── test_v52_ui_design_system.py  # Theme + 硬编码扫描
 ├── test_v52_ui_polish.py
 └── ... (32 v52 files total)
```

### 当前测试状态

- 自定义 check runner（非 pytest）
- 覆盖：单元测试 / 架构扫描 / 存储测试 / UI 一致性检查
- 最新全量回归：**PASS（v5.2.3 基线 988/988，见 `docs/reports/v5.2.3_release_audit.md` §四）**

> 测试项数量随环境与阶段变化，不在此固化数字。精确数字见各 RC/Phase 报告与基线文件（`logs/baseline_v5.2.3.txt`）。

### 已知环境问题

- `test_v52_phase0` / `test_v52_phase2` 在部分环境以 `0xC0000005` 崩溃（原生库访问冲突）
- 详见 `docs/reports/rc5_environment_notes.md`

---

## 11. 当前技术债

| # | 问题 | 优先级 | 说明 |
|---|------|--------|------|
| 1 | common/theme.py 迁移 | P2 | Agent legacy 色板，留给 Phase 4-7 Agent GUI |
| 2 | Storage schema migration path | P2 | schema v2 出现时需要迁移机制 |
| 3 | common/protocol.py 遗留 | P2 | v4 TCP 协议残留，标记为 legacy |
| 4 | common/gui/detail_panel.py | P2 | Agent 侧自包含实现，与 host 版本功能重复 |
| 5 | Retention Settings 集成 | P2 | 保留策略 UI 配置，留给 Phase 5-5C |
| 6 | Agent GUI 未升级 | P3 | 仍为 v5.1 旧风格仪表盘 |
| 7 | i18n 未统一 | P3 | common/i18n + zh_CN.json/en.json，host/agent 分别引用 |

### 已解决（历史记录）

| 问题 | 解决方式 |
|------|----------|
| Theme 重复 token 来源 | RC-7 Theme Token Consolidation |
| Settings Page facade 泄漏 | Phase 4-6A VM/Facade 边界修复 |
| 重复 save 写盘 | Phase 4-6A dirty/save 模型 |
| Alert 假绑定 | Phase 4-6A Alert Rule 重构 |

---

## 12. Roadmap

### Phase 4-6: Settings Redesign（COMPLETE ✅）

**已完成**:
- VM boundary cleanup（set 不持久化，save 统一提交）
- Facade isolation（删除 facade property 泄漏）
- dirty/save 模型
- Sidebar + 5 sections 布局
- save 反馈（✓ Saved）
- settings flow tests

### Phase 4-7: Agent GUI Upgrade（Future）

**目标**: Agent 本机仪表盘与 Host 视觉统一

**技术方向**:
- 复用 Host Theme + Widgets
- 通过 common/theme_tokens 实现跨端 token 共享
- 迁移 common/theme.py legacy 色板

### Phase 5: Storage Expansion（COMPLETE ✅）

**目标**: 持久化历史数据，支持趋势分析

| 子阶段 | 内容 | 状态 |
|--------|------|------|
| 5-1 | Storage Foundation (SQLite + schema + repository) | ✅ COMPLETE |
| 5-2 | Metrics Persistence (Frame → Record 写入) | ✅ COMPLETE |
| 5-3 | History Query API (range/latest/aggregate) | ✅ COMPLETE |
| 5-4 | History UI (历史趋势页) | ✅ COMPLETE |
| 5-5 | Retention (5-5A Foundation + 5-5B Startup) | ✅ COMPLETE |

**技术方向**:
- SQLite 时间序列存储
- Repository 抽象层
- Collector → Service → Repository → SQLite

### Phase 6: Advanced Alert Engine（Future）

**目标**: 规则引擎 + 告警生命周期

**技术方向**:
- 事件系统 (event/)
- 告警恢复检测
- 多级告警 (INFO/WARNING/CRITICAL)

### Phase 7: UX Optimization（Future）

**目标**: 交互体验提升

**技术方向**:
- Dashboard 自定义布局
- 键盘快捷键
- 拖拽排序

### Phase 8+: Service Architecture（Future）

**目标**: 从桌面应用演进为服务化架构

**技术方向**:
- REST API 暴露 Host 功能
- 多用户权限
- 云端部署

---

## 13. AI 开发指南

### 修改代码前必须

1. **阅读 `docs/core/ARCHITECTURE.md`** — 确认架构分层
2. **确认数据流** — Page ← VM ← Store，不跳层
3. **检查已有组件** — `host/gui/widgets/` 避免重复造轮子
4. **运行相关测试** — `python tests/test_v52_xxx.py`
5. **禁止破坏分层** — Page 不碰 Store，Widget 不碰业务

### 新增 Widget 检查清单

- [ ] 继承 QFrame / QWidget
- [ ] 使用 ThemeColors / ThemeSpacing
- [ ] 无硬编码颜色
- [ ] 无业务逻辑
- [ ] 添加测试

### 新增 Page 检查清单

- [ ] 继承 PageBase
- [ ] 实现 set_view_model() / on_show() / on_hide()
- [ ] 只导入 Widget + ViewModel
- [ ] 不访问 Store / ConfigManager
- [ ] 在 MainWindow 注册
- [ ] 添加测试

### 常见错误

| 错误 | 正确做法 |
|------|----------|
| `from host.store import FrameStore` (在 Page 中) | 通过 VM 间接访问 |
| `color="#ffffff"` (在 Widget 中) | `color={TC.TEXT_PRIMARY}` |
| `vm._facade._mgr.get_xxx()` | 走 Facade 公开接口 |
| `QTimer` 轮询刷新 | Signal 驱动 |

---

## 附录: 文档结构

```
docs/
├── core/         当前开发规范与架构文档
├── phases/       Phase 历史记录
├── reports/      RC 审计、验证和分析报告
└── archive/      已归档的历史设计和迁移资料
```
