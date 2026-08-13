# 当前阶段和未来计划

> **Version**: v5.2 Phase4
> **Status**: CURRENT

## 当前阶段

**Phase 4: UI Upgrade**

### 已完成

| Phase | 内容 | 状态 |
|-------|------|------|
| Phase 3-3 | NodeDetailViewModel | ✅ COMPLETE |
| Phase 3-4 | AlertsPage | ✅ COMPLETE |
| Phase 3-5 | MonitorPage | ✅ COMPLETE |
| Phase 3-6 | SettingsPage | ✅ COMPLETE |
| Phase 3-7 | Widget Migration | ✅ COMPLETE |
| Phase 3-8 | MainWindow Refactor | ✅ COMPLETE |
| Phase 3-9 | Theme System | ✅ COMPLETE |
| Phase 4-1 | Design System | ✅ COMPLETE |
| Phase 4-2 | App Shell | ✅ COMPLETE |
| Phase 4-3 | NodesPage Redesign | ✅ COMPLETE |
| Phase 4-4 | MonitorPage Redesign | ✅ COMPLETE |
| Phase 4-5 | Audit | ✅ COMPLETE |
| Phase RC-1 | 文档体系整理 | ✅ COMPLETE |
| Phase RC-2 | 文档体系重构 | ✅ COMPLETE |

### 进行中

| Phase | 内容 | 状态 |
|-------|------|------|
| Phase 4-5 | AlertsPage Redesign | 🔄 待开始 |
| Phase 4-6 | SettingsPage Redesign | 🔄 待开始 |

### 待完成

| Phase | 内容 | 优先级 |
|-------|------|--------|
| 硬编码颜色清理 (25处) | P1 |
| common/theme 迁移 (8处) | P1 |
| Alerts UI Redesign | P2 |
| Settings UI Redesign | P2 |
| Performance Optimization | P3 |
| Agent GUI 升级 | P3 |

## 未来计划

### v5.3 (短期)

- 完成所有页面 UI Redesign
- 清理硬编码颜色
- 迁移 common/theme 到 host/gui/theme
- 性能优化

### v6.0 (中期)

| 模块 | 说明 |
|------|------|
| storage/ | 历史存储 (SQLite) |
| event/ | 事件系统 |
| history/ | 历史查询 API |
| manager/ | 节点状态 / watchdog |

### v7.0 (长期)

- Electron/Qt6 迁移
- 多用户权限
- 云端部署
- 插件系统

## 测试状态

| 指标 | 值 |
|------|-----|
| 测试文件 | 27 个 |
| 测试项 | 600+ |
| 通过率 | 100% |
| 最后验证 | 2026-08-12 |
