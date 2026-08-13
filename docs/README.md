# PC Monitor — 文档总入口

> **Version**: v5.2 + Phase4 UI Upgrade
> **Status**: CURRENT

## 项目介绍

PC Monitor 是一套**局域网远程电脑监控系统**，采用双角色架构：

- **Agent**（副机端）：运行在每台被监控电脑上，采集硬件数据并推送
- **Host**（主机端）：运行在监控电脑上，集中展示所有节点的实时状态

## 当前版本

**v5.2 + Phase4 UI Upgrade**

| 模块 | 版本 | 状态 |
|------|------|------|
| Agent | v5.0 | ✅ COMPLETE |
| Host Backend | v5.2 | ✅ COMPLETE |
| Host Architecture | v5.2 | ✅ COMPLETE |
| Design System | v5.2 Phase4 | ✅ COMPLETE |
| Dashboard UI | v5.2 Phase4 | ✅ COMPLETE |
| Nodes UI | v5.2 Phase4 | ✅ COMPLETE |
| Monitor UI | v5.2 Phase4 | ✅ COMPLETE |
| Alerts UI | v5.2 Phase4 | 🔄 IN PROGRESS |
| Settings UI | v5.2 Phase4 | 🔄 IN PROGRESS |

## 核心架构

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

## 快速导航

### 核心文档（开发必读）

| 文档 | 说明 |
|------|------|
| [core/ARCHITECTURE.md](core/ARCHITECTURE.md) | 当前最终架构 |
| [core/DATA_FLOW.md](core/DATA_FLOW.md) | 数据流说明 |
| [core/UI_SYSTEM.md](core/UI_SYSTEM.md) | 唯一 UI 设计规范 |
| [core/DEVELOPMENT.md](core/DEVELOPMENT.md) | 开发规范 |
| [core/ROADMAP.md](core/ROADMAP.md) | 当前阶段和未来计划 |

### 参考文档

| 文档 | 说明 |
|------|------|
| [core/PRODUCT.md](core/PRODUCT.md) | 产品定位与功能 |
| [core/API_PROTOCOL.md](core/API_PROTOCOL.md) | Agent/Host 通信协议 |

> 旧的 architecture.md / protocol.md / api.md 已整合进 core/，原始文件归档在 [archive/](archive/)。

### 历史文档

| 目录 | 说明 |
|------|------|
| [phases/](phases/) | Phase 3 迁移历史 |
| [reports/](reports/) | 审计与清理报告 |
| [archive/](archive/) | 归档的旧版设计文档 |

## 目录结构

```
docs/
├── README.md              ← 你在这里
├── core/                  ⭐ 开发必读
│   ├── PRODUCT.md
│   ├── ARCHITECTURE.md
│   ├── UI_SYSTEM.md
│   ├── DATA_FLOW.md
│   ├── API_PROTOCOL.md
│   ├── DEVELOPMENT.md
│   └── ROADMAP.md
├── phases/                Phase 迁移历史
├── reports/               审计/清理报告
└── archive/               归档旧文档（含旧 architecture/protocol/api/installation/ui_design 等）
```

## AI 开发指南

如果你是 AI 助手，只需阅读以下文件即可理解整个项目：

1. **docs/README.md**（本文件）— 项目概览
2. **docs/core/ARCHITECTURE.md** — 架构和目录
3. **docs/core/DATA_FLOW.md** — 数据流
4. **docs/core/UI_SYSTEM.md** — UI 规范
5. **docs/core/DEVELOPMENT.md** — 开发规范
