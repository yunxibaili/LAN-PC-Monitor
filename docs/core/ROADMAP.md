# 当前阶段和未来计划

> **Version**: v5.2.3
> **Status**: STABLE（v5.2.x 已发布，v5.3 规划中）

## 当前阶段

**v5.2.3 — Architecture Stabilization Release（已发布）**

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
| v5.2 Stabilization | 架构冻结 + Release 发布 | ✅ COMPLETE |
| v5.2.3 Storage & History Infrastructure | 发布文档闭环 + 基线冻结（988/988） | ✅ COMPLETE |

### 进行中

| Phase | 内容 | 状态 |
|-------|------|------|
| （无） | v5.2.x 已冻结，仅修 P0 缺陷 | — |

### 待完成（v5.3 及以后）

| Phase | 内容 | 优先级 |
|-------|------|--------|
| v5.3-0 | Repository hygiene（CHANGELOG / README badge / Release 流程固定 / Issue & PR 模板） | P2 |
| v5.3-1 | netifaces 替换（psutil.net_if_addrs / ifaddr） | P2 |
| v5.3-2 | history.db 路径统一 | P2 |
| v5.3-3 | Settings dirty 双模型收敛 | P2 |
| v5.3-4 | Agent/Host Theme 统一（common/theme.py 迁移） | P2 |
| 5-5C | Retention Settings 集成 | P2 |
| 6 | 高级告警引擎 | P2 |
| 7 | UX 优化 | P3 |

> v5.2.x 已冻结（见 `docs/releases/v5.2.x_freeze.md`），仅修崩溃/安全/发布阻塞缺陷。
> 已登记问题清单见 `docs/issues/v5.2.3_known_issues.md`。

## 未来计划

> **发布后节奏**：v5.2.3 发布后先**观察 1~2 周**收集 Issue（平台期，稳定 API 优先），
> 再开工 v5.3-0 hygiene，最后进入 v5.3 feature。不要发布后立即堆功能。

### 短期（v5.3 P2 Cleanup Sprint）

- v5.3-0: Repository hygiene（CHANGELOG / README badge / Release 流程固定 / Issue & PR 模板）
- v5.3-1: netifaces 替换（CI 已暴露无 cp310+ wheel）
- v5.3-2: history.db 路径统一（storage_service / config / 用户数据目录）
- v5.3-3: Settings dirty 双模型合并
- v5.3-4: Agent/Host Theme 统一（含 common/theme.py 迁移）
- Phase 5-5C: Retention Settings 集成

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
- 覆盖：VM / Page / Widget / Storage / Retention / Flow / Theme / 架构扫描
- 最新全量回归：**PASS（v5.2.3 基线 988/988）**

> 测试项数量随环境与阶段变化，不在此固化数字。精确基线见：
> `docs/reports/v5.2.3_release_audit.md` §四 与 `docs/reports/baseline_v5.2.3.txt`。
