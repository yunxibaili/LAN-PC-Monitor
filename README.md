# LAN PC Monitor

轻量级局域网硬件监控平台，支持多节点实时监控、历史趋势分析、事件告警。

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]() [![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)]()

> 实时查看多台 Windows 电脑的 CPU / GPU / 内存 / 磁盘 / 网络 / FPS / 进程，并逐步演进为带历史分析、事件告警的轻量级监控平台。纯局域网运行，不依赖云服务。

---

## Current Version

- **版本**：v5.2 + Phase4 UI Upgrade
- **状态**：Current（已实现）
- **架构**：前后端分离（Agent 服务端 + Host 监控端）
- **通信**：WebSocket + REST API
- **UI**：SaaS 深色风格，Design System 统一主题

## Architecture

```
Agent (采集+推送)
  ↓ WebSocket
Connection (WS 客户端)
  ↓ Signal
Store (数据存储)
  ↓
ViewModel (数据转换)
  ↓
Page (页面容器)
  ↓
Widget (UI 组件)
  ↓
Theme (设计系统)
```

详细架构见 [docs/core/ARCHITECTURE.md](docs/core/ARCHITECTURE.md)。

## Features

### Host 5 个页面

| 页面 | 功能 | 状态 |
|------|------|------|
| Dashboard | 节点总览、KPI 统计、趋势图 | ✅ COMPLETE |
| Nodes | 节点管理、搜索过滤、详情仪表盘 | ✅ COMPLETE |
| Monitor | 单节点深度监控、实时图表 | ✅ COMPLETE |
| Alerts | 告警列表、筛选过滤 | 🔄 IN PROGRESS |
| Settings | 通用/告警/节点/外观/高级 | 🔄 IN PROGRESS |

### 核心能力

- 实时监控：CPU / GPU / 内存 / 磁盘 / 网络 / FPS / 进程
- 多节点管理：零配置自动发现（mDNS + UDP）
- 高性能通信：WebSocket 每秒推送
- 红线告警：指标超阈值自动告警
- Design System：统一颜色/字体/间距

## Quick Start

```bash
# Agent（被监控端）
python -m agent              # 后台服务
python -m agent --gui        # 带本机仪表盘

# Host（监控端）
python -m host               # 集中监控大屏
```

首次启动自动生成配置文件。详细安装见 [docs/archive/installation.md](docs/archive/installation.md)。

## Documentation

```
docs/
├── README.md              文档总入口
├── core/                  ⭐ 开发必读
│   ├── ARCHITECTURE.md    最终架构
│   ├── UI_SYSTEM.md       UI 设计规范（唯一权威）
│   ├── DATA_FLOW.md       数据流
│   ├── DEVELOPMENT.md     开发规范
│   └── ROADMAP.md         路线图
├── phases/                Phase 迁移历史
├── reports/               审计/清理报告
└── archive/               历史归档
```

开发人员和 AI 只需阅读 `docs/README.md` + `docs/core/*.md` 即可理解整个项目。

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

开发指南见 [docs/core/DEVELOPMENT.md](docs/core/DEVELOPMENT.md)。

## Roadmap

### v5.2（当前）

- [x] Design System 统一主题
- [x] App Shell (HeaderBar + SideNav)
- [x] Dashboard UI 升级
- [x] Nodes UI 升级
- [x] Monitor UI 升级
- [ ] Alerts UI 升级
- [ ] Settings UI 升级
- [ ] 硬编码颜色清理

### v6.0（规划中）

- [ ] 历史数据库（SQLite）
- [ ] 事件规则系统
- [ ] WebSocket 订阅模式

详细路线图见 [docs/core/ROADMAP.md](docs/core/ROADMAP.md)。

## License

MIT
