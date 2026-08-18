# LAN PC Monitor

轻量级局域网硬件监控平台，支持多节点实时监控、历史趋势分析、事件告警。

[![Windows Tests](https://github.com/yunxibaili/LAN-PC-Monitor/actions/workflows/windows-tests.yml/badge.svg)](https://github.com/yunxibaili/LAN-PC-Monitor/actions/workflows/windows-tests.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]() [![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)]() [![Version](https://img.shields.io/badge/Version-v5.2.3-green.svg)]() [![License](https://img.shields.io/badge/License-MIT-blue.svg)]()

> 实时查看多台 Windows 电脑的 CPU / GPU / 内存 / 磁盘 / 网络 / FPS / 进程，并逐步演进为带历史分析、事件告警的轻量级监控平台。纯局域网运行，不依赖云服务。

---

## Current Version

- **版本**：v5.2.3（Architecture Stabilization Release）
- **状态**：Stable（已冻结）
- **架构**：前后端分离（Agent 服务端 + Host 监控端）
- **通信**：WebSocket + REST API
- **UI**：SaaS 深色风格，Design System 统一主题
- **存储**：SQLite 持久化（指标 / 告警 / 会话 + 保留策略）

## Architecture

```
Agent (采集+推送)
  ↓ WebSocket
Connection (WS 客户端)
  ↓ Signal
DataController
  ├── Store (FrameStore / NodeStore / HistoryStore / AlertStore)
  ├── MetricPersistenceService → StorageService → Repository / Retention → SQLite
  └── ViewModel → Page → Widget → Theme
```

持久化数据路径：

```
Collector
   ↓
DataController
   ↓
MetricPersistenceService
   ↓
StorageService
   ↓
+----------------+
|                |
v                v
Repository      Retention
   ↓
HistoryFacade
   ↓
HistoryVM
   ↓
HistoryPage
```

详细架构见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## Features

### Real-time Monitoring

- ✅ Collector architecture（CPU / GPU / 内存 / 磁盘 / 网络 / FPS / 进程）
- ✅ Multi-node monitoring（零配置自动发现 mDNS + UDP）
- ✅ Live dashboard（Dashboard / Nodes / Monitor 实时大屏）

### Alert System

- ✅ Alert rules（红线阈值，30s 去重）
- ✅ Alert state tracking（AlertStore + AlertEngine）
- ✅ Alert persistence（SQLite 告警历史）

### Settings Redesign

- ✅ MVVM isolation（VM/Facade 边界，set 不落盘）
- ✅ Sidebar navigation（5 分区布局）
- ✅ Dirty tracking（统一 dirty/save 模型）
- ✅ Save feedback（✓ Saved 反馈）

### Storage Infrastructure

- ✅ SQLite storage layer（`host/storage`）
- ✅ Repository abstraction（metrics / alerts / sessions）
- ✅ Versioned schema（schema 版本管理）

### History System

- ✅ History Query API（range / latest / aggregate）
- ✅ History charts（HistoryPage 趋势图）
- ✅ Metrics persistence（Frame → Record 写入）

### Data Lifecycle

- ✅ Retention policy（保留策略）
- ✅ Startup cleanup（启动清理）

### 页面（6 页全部 COMPLETE）

| 页面 | 功能 | 状态 |
|------|------|------|
| Dashboard | 节点总览、KPI 统计、趋势图 | ✅ COMPLETE |
| Nodes | 节点管理、搜索过滤、详情仪表盘 | ✅ COMPLETE |
| Monitor | 单节点深度监控、实时图表 | ✅ COMPLETE |
| Alerts | 告警列表、筛选过滤 | ✅ COMPLETE |
| History | 历史趋势查询、图表 | ✅ COMPLETE |
| Settings | 通用/告警/节点/外观/高级 | ✅ COMPLETE |

## Quick Start

```bash
# Agent（被监控端）
python -m agent              # 后台服务
python -m agent --gui        # 带本机仪表盘

# Host（监控端）
python -m host               # 集中监控大屏
```

首次启动自动生成配置文件。详细安装见 [docs/archive/old_docs/installation.md](docs/archive/old_docs/installation.md)。

## Documentation

```
docs/
├── README.md              文档总入口
├── ARCHITECTURE.md        架构 + 数据流
├── UI_GUIDE.md            ⭐ UI 唯一规范
├── DEVELOPMENT.md         开发规范
├── ROADMAP.md             路线图
├── known_issues.md        已知问题
├── releases/              Release Notes + 审计
└── archive/               历史文档（phases/reports/old_docs）
```

开发人员和 AI 只需阅读 `docs/README.md` + `docs/UI_GUIDE.md` 即可理解整个项目。

## Configuration

| 端 | 配置文件 | 说明 |
|----|----------|------|
| Agent | `agent_config.json` | 端口、token、采集器开关 |
| Host | `host_config.json` | 节点列表、告警规则 |

## Development

```bash
pip install -r requirements-agent.txt -r requirements-host.txt
python tests/test_api.py    # REST + WebSocket 端到端
python tests/test_p0.py     # 协议/采集器冒烟
```

测试基线（不写死数量，见审计报告）：

```
Latest verified baseline:
  docs/releases/v5.2.3_release_audit.md  (§四 测试基线冻结)
  docs/releases/baseline_v5.2.3.txt      (逐文件明细)
```

开发指南见 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)。

## Roadmap

### v5.2（已发布：v5.2.3）

- [x] Design System 统一主题
- [x] App Shell (HeaderBar + SideNav)
- [x] Dashboard / Nodes / Monitor UI 升级
- [x] Alerts UI 升级（Phase 4-5）
- [x] Settings UI 升级（Phase 4-6）
- [x] SQLite 持久化（Phase 5-1 ~ 5-5）
- [x] History 查询与图表（Phase 5-3 / 5-4）
- [x] Retention 清理（Phase 5-5）

### v5.3（规划中）

- [ ] history.db 路径统一（P2）
- [ ] Settings dirty 双模型收敛（P2）
- [ ] Agent GUI 升级（Phase 4-7，含 common/theme.py 迁移）
- [ ] 高级告警引擎（Phase 6）

详细路线图见 [docs/ROADMAP.md](docs/ROADMAP.md)。

## License

MIT
