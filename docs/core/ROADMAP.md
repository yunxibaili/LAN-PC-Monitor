# 当前阶段和未来计划

> **Version**: v5.2.2
> **Status**: CURRENT

## 当前阶段

**Phase 5: Data Lifecycle — 已完成主线**

### 已完成

| Phase | 内容 | 状态 |
|-------|------|------|
| Phase 3-3~3-9 | MVVM 架构迁移 | ✅ COMPLETE |
| Phase 4-1 | Design System | ✅ COMPLETE |
| Phase 4-2 | App Shell | ✅ COMPLETE |
| Phase 4-3 | NodesPage Redesign | ✅ COMPLETE |
| Phase 4-4 | MonitorPage Redesign | ✅ COMPLETE |
| Phase 4-5 | AlertsPage Redesign + Final Polish | ✅ COMPLETE |
| Phase 4-6 | SettingsPage Redesign (A/B/C) | ✅ COMPLETE |
| Phase RC-1~6 | 文档整理 + 代码清理 + 基线冻结 | ✅ COMPLETE |
| RC-7 | Theme Token Consolidation | ✅ COMPLETE |
| Phase 5-1 | Storage Foundation (SQLite + schema + repository) | ✅ COMPLETE |
| Phase 5-2 | Metrics Persistence | ✅ COMPLETE |
| Phase 5-3 | History Query API | ✅ COMPLETE |
| Phase 5-4 | History UI | ✅ COMPLETE |
| Phase 5-5 | Retention (5-5A Foundation + 5-5B Startup Trigger) | ✅ COMPLETE |

### 进行中

| Phase | 内容 | 状态 |
|-------|------|------|
| Project Cleanup | 发布前工程整理 | 🔄 进行中 |

### 待完成

| Phase | 内容 | 优先级 |
|-------|------|--------|
| 5-5C | Retention Settings 集成 | P2 |
| 4-7 | Agent GUI 升级 | P3 |
| 6 | 高级告警引擎 | P2 |
| 7 | UX 优化 | P3 |

## 未来计划

### 短期

- Phase 5-5C: Retention Settings 集成
- Phase 4-7: Agent GUI 升级（含 common/theme.py 迁移）

### 中期

| 模块 | 说明 |
|------|------|
| event/ | 事件系统 |
| 高级告警 | 告警恢复检测 / 多级告警 |
| Storage migration | schema v2 迁移机制 |

### 长期

- Electron/Qt6 迁移
- 多用户权限
- 云端部署
- 插件系统

## 测试状态

- 框架：自定义 check runner（非 pytest）
- 最新全量回归：**PASS**（929+ 项）
- 覆盖：VM / Page / Widget / Storage / Retention / Flow / Theme / 架构扫描

> 测试项数量随环境与阶段变化，精确数字见各 Phase 报告。
