# Project Cleanup Plan

> **Generated**: 2026-08-13
> **性质**: 审计后的清理规划，未执行
> **原则**: 不修改业务逻辑、不重构大型模块、不添加新功能

---

## P0 — 立即执行（发布阻塞）

| # | 任务 | 说明 | 风险 |
|---|------|------|------|
| 1 | git push（4 commit + 5 tag） | main 领先 origin/main 4 个 commit | 无，纯同步 |
| 2 | 统一 `service` 目录命名 | `host/services/metric_persistence.py` → `host/service/metric_persistence.py` | 低，需同步 import + 测试路径 |
| 3 | 接入 MetricPersistenceService | DataController 调用 persist_frame，让数据真正持久化 | 中，需确认调用时机 |

## P1 — 近期执行

| # | 任务 | 说明 |
|---|------|------|
| 4 | 消除 SummaryCard 重复 | dashboard_page 复用 chart_panel.SummaryCard（注意接口差异） |
| 5 | gitignore history.db / *.db | 防止运行时数据库文件入库 |
| 6 | 同步 ARCHITECTURE.md | 补 storage/、services/、history 组件 |

## P2 — 计划内（关联已有 Phase）

| # | 任务 | 归属 Phase |
|---|------|-----------|
| 7 | Storage schema migration 机制 | 未来 schema v2 |
| 8 | common/theme.py 迁移 | Phase 4-7 Agent GUI |
| 9 | common/protocol.py 归档/删除 | 独立清理 |
| 10 | common/gui/detail_panel.py 统一 | Phase 4-7 |
| 11 | 同步 ROADMAP.md / DEVELOPMENT.md | 文档收口 |

## P3 — 可选优化

| # | 任务 | 归属 Phase |
|---|------|-----------|
| 12 | Agent GUI 升级 | Phase 4-7 |
| 13 | i18n 统一 | 后续 |
| 14 | Retention Settings 集成 | Phase 5-5C |

---

## 执行顺序

```
P0-1  git push（先同步基线）
  ↓
P0-2  service 目录统一（纯移动，改 import）
  ↓
P0-3  接入 MetricPersistenceService
  ↓
P1-4  SummaryCard 去重
P1-5  gitignore *.db
P1-6  ARCHITECTURE 同步
  ↓
P2    文档同步 + 关联 Phase
```

## 风险提示

- P0-3（接入 MetricPersistence）涉及数据流改动，需谨慎确认调用时机（DataController._on_data 内，与 FrameStore/HistoryStore 同级）。
- P1-4（SummaryCard 去重）接口不同（dashboard 有 value 初始值 + 28px，chart_panel 有 sub + 20px），需统一接口或保留两个变体。
- P0-2（目录移动）需同步 `tests/test_metric_persistence.py` 的 import 路径和源码扫描路径。
