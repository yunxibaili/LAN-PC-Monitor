# Project Full Technical Audit Report

> **Generated**: 2026-08-13
> **性质**: 只读审计，未修改任何代码
> **原则**: 以当前代码 / 目录 / 测试 / Git 真实状态为准

---

## 1. 当前架构（真实）

```
Application
│
├── host/          (98 files, 7905 lines)
│   ├── gui/
│   │   ├── pages/        (7 页: dashboard/nodes/monitor/alerts/history/settings + base)
│   │   ├── widgets/      (20 活跃 + 4 归档)
│   │   ├── theme/        (colors/spacing/typography/formatters/components/style)
│   │   ├── navigation/   (side_nav)
│   │   └── controllers/  (navigation/data/alert/window)
│   ├── viewmodels/       (6 VM: dashboard/node_detail/monitor/alert/history/settings)
│   ├── facade/           (settings/history/alert_adapter/connection_factory)
│   ├── service/          (alert/discovery/storage)
│   ├── services/         ⚠️ (metric_persistence, 目录命名异常)
│   ├── storage/          (database/schema/records/retention/repositories)
│   ├── store/            (frame/node/history/alert/signals)
│   ├── manager/          (tray_manager)
│   ├── config.py / connection.py / connection_core.py / discovery.py / alerts.py
│   └── local_node.py / main.py
│
├── agent/          (12 files, 1073 lines)
│   ├── main.py / aggregator / http_server / websocket_server / discovery / config
│   └── gui/ (main_window)
│
└── common/         (30 files, 2889 lines)
    ├── collectors/       (cpu/gpu/ram/disk/net/fps/proc/sys/net_quality + base)
    ├── config_manager / theme / theme_tokens / i18n / quality / utils
    └── gui/ (detail_panel)
```

### 数据流

```
Agent Collector → Aggregator → WebSocket
    ↓
Host DataController → FrameStore/HistoryStore/NodeStore/AlertStore
    ├── AlertService (红线检测)
    └── MetricPersistenceService (5-2, ⚠️ 未接入 DataController)
         ↓
    MetricsRepository → SQLite (host/storage/)
         ├── HistoryFacade → HistoryVM → HistoryPage (5-3/5-4)
         └── RetentionService → delete_before (5-5)
```

---

## 2. 架构边界审核（全通过）

| 检查项 | 结果 |
|--------|------|
| Page → Store/ConfigManager/sqlite3/storage | ✅ 0 处 |
| Widget → Store/VM/storage | ✅ 0 处 |
| ViewModel → PyQt5/sqlite3/storage | ✅ 0 处 |
| common → host | ✅ 0 处 |

---

## 3. 技术栈确认

| 层 | 技术 | 状态 |
|----|------|------|
| GUI | PyQt5 | ✅ |
| Charts | pyqtgraph（惰性导入 + fallback） | ✅ |
| Storage | SQLite (schema v1) | ✅ |
| Testing | 自定义 check runner（非 pytest） | ✅ |
| Config | JSON (agent/host_config.json) | ✅ |
| 通信 | HTTP REST + WebSocket | ✅ |

---

## 4. 代码质量审核

### 4.1 重复代码

| # | 重复项 | 位置 | 严重度 |
|---|--------|------|--------|
| 1 | `SummaryCard` 类 | dashboard_page.py + chart_panel.py | P1 |
| 2 | `DetailPanel` | common/gui + host/gui/widgets（Agent/Host 分版） | P2 |
| 3 | `LocalCollectorPack` | host/local_node + agent/local_node | P3（角色不同，有意） |

### 4.2 目录命名不一致

| 问题 | 现状 | 严重度 |
|------|------|--------|
| `service` vs `services` | metric_persistence 在 `host/services/`（复数，无 `__init__.py`），其余在 `host/service/` | **P1** |

### 4.3 Dead Code / 悬空能力

| 项 | 状态 | 严重度 |
|----|------|--------|
| MetricPersistenceService | 已实现 + 有测试，但**未接入 DataController**（数据持久化未真正生效） | **P1** |
| host/gui/widgets/archive/ (4 文件) | 已归档，保留 | 正常 |
| common/protocol.py | v4 TCP 遗留 | P2 |

### 4.4 TODO/FIXME

无 TODO / FIXME 残留。✅

---

## 5. Theme / Design System 审核

| Token 层 | 状态 |
|----------|------|
| common/theme_tokens.py | ✅ Production（Host 接线） |
| host/gui/theme/* | ✅ Production |
| common/theme.py | Legacy（Agent 用，Phase 4-7 迁移） |

硬编码颜色（host/gui 非 theme）：**0 处** ✅

---

## 6. Storage / Data Pipeline 审核

| 检查项 | 结果 |
|--------|------|
| sqlite3 仅 storage/database.py | ✅ |
| UI → Storage 直连 | ✅ 0 处 |
| schema 版本 | v1 |
| migration 机制 | ⚠️ 无（schema v2 时需要） |
| Retention | 5-5A/5-5B 完成 |

---

## 7. 测试体系审核

- 框架：自定义 check runner（非 pytest）
- 测试文件：37 个
- 全量回归：**924 passed, 0 failed**

覆盖：VM / Page / Widget / Storage / Retention / Flow / Theme / 架构扫描

缺失测试：MetricPersistence 数据流集成（因未接入 DataController）

---

## 8. 历史遗留问题

| 项 | 分类 | 建议 |
|----|------|------|
| common/protocol.py (v4 TCP) | Legacy | 归档或删除 |
| common/theme.py | Legacy | Phase 4-7 迁移 |
| common/gui/detail_panel.py | 重复 | Phase 4-7 统一 |
| host/gui/widgets/archive/ | 归档 | 保留 |

---

## 9. 文档一致性审核

| 文档 | 状态 |
|------|------|
| BLUEPRINT.md | ✅ 已同步至 v5.2.2 / Phase 5 完成 |
| ARCHITECTURE.md | ⚠️ 未含 storage/、services/、history 组件 |
| ROADMAP.md | ⚠️ 停留 Phase 4-6，未反映 Phase 5 |
| DEVELOPMENT.md | ⚠️ 未含 Storage 层开发规范 |

---

## 10. Git 审核

| 项 | 状态 |
|----|------|
| 工作区 | ✅ clean |
| 分支 | main（单一主干） |
| 本地 tag | v4.0.0, v5.2-rc1, v5.2-stable, v5.2.1, v5.2.2 |
| 提交链 | 连续，无空提交 |

---

## 11. GitHub 同步审核

| 项 | 状态 |
|----|------|
| remote | https://github.com/yunxibaili/LAN-PC-Monitor.git |
| 本地 vs remote | ⚠️ **main 领先 origin/main 4 个 commit** |
| 未推送 commit | RC1, v5.2-stable, v5.2.1, v5.2.2 |
| 未推送 tag | v5.2-rc1, v5.2-stable, v5.2.1, v5.2.2 |

---

## 12. Release Readiness

| 维度 | 状态 |
|------|------|
| Architecture | ✅ |
| Code Quality | ⚠️（services/ 命名 + SummaryCard 重复 + MetricPersistence 未接入） |
| Documentation | ⚠️（ARCHITECTURE/ROADMAP/DEVELOPMENT 未同步 Phase 5） |
| Testing | ✅ 924/924 |
| Git Release | ⚠️（领先 remote 4 commit 未 push） |
