# Phase RC-1 文档体系整理报告

> **审计时间**: 2026-08-12
> **审计目标**: 将 docs/ 从开发状态整理为 Release Candidate 状态
> **原则**: 只修改 docs/，不修改 Python 代码

---

## 一、执行摘要

| 任务 | 状态 |
|------|------|
| 创建唯一权威设计文档 | ✅ `docs/design/ui_design_system.md` |
| 移动旧 UI 文档到 archive | ✅ 3 个文件 |
| 移动历史审计文档到 archive | ✅ 3 个文件 |
| 为 6 个 phase 文档添加 Status | ✅ 完成 |
| 更新 host.md 目录树 | ✅ 完成 |
| 创建 rc_document_audit.md | ✅ 本文件 |

---

## 二、文档数量变化

| 指标 | 整理前 | 整理后 |
|------|--------|--------|
| docs/ 根目录 md 文件 | 29 | 20 |
| docs/design/ | 0 | 1 |
| docs/archive/ | 0 | 6 |
| **总计** | **29** | **27** |

减少原因：3 个旧 UI 设计文档被移入 archive（不删除），3 个历史审计文档移入 archive。

---

## 三、冲突文档处理

### 3.1 原 4 个 UI 设计文档

| 文件 | 处理 | 原因 |
|------|------|------|
| `ui_design.md` (v5.0) | → `archive/ui_design_v50.md` | v5.0 设计，已被 v5.2 取代 |
| `unified_ui_design.md` | → `archive/unified_ui_design.md` | 与 spec 重叠，颜色冲突 |
| `v5.2_ui_design.md` | → `archive/v52_ui_design_legacy.md` | 路径/模块名过期 |
| `ui_design_spec_v52.md` | **保留** (根目录) | 最接近当前实现 |

### 3.2 新建权威文档

**`docs/design/ui_design_system.md`** — 唯一权威 UI 设计规范

内容来源合并：
- `ui_design_spec_v52.md` → 颜色/字体/间距/组件规范
- `v5.2_ui_design.md` → 架构分层/页面布局
- `unified_ui_design.md` → 双端差异说明
- `ui_design.md` → 阈值变色规范

---

## 四、Phase 文档状态标记

| 文件 | Status | Date | Result |
|------|--------|------|--------|
| `phase_3_3a_design.md` | ✅ COMPLETE | 2026-08-11 | NodeDetailVM 89 项测试 |
| `phase_3_3c_detail_panel_design.md` | ✅ COMPLETE | 2026-08-11 | DetailPanel 48 项测试 |
| `phase_3_4_alerts_design.md` | ✅ COMPLETE | 2026-08-11 | AlertsPage 30 项测试 |
| `phase_3_5_monitor_design.md` | ✅ COMPLETE | 2026-08-12 | MonitorPage 67 项测试 |
| `phase_3_6_settings_design.md` | ✅ COMPLETE | 2026-08-11 | SettingsPage 30 项测试 |
| `phase_3_7_widget_migration.md` | ✅ 完成 | 2026-08-11 | 已有标记 |
| `phase_3_8_main_window_refactor.md` | ✅ 完成 | 2026-08-12 | 已有标记 |
| `phase_3_9_theme_audit.md` | ✅ COMPLETE | 2026-08-11 | Theme 系统收敛 |

---

## 五、host.md 更新

### 修正内容

| 项目 | 旧 | 新 |
|------|-----|-----|
| 版本 | v5.0 | v5.2 (Phase 4) |
| 目录树 | 含 overview_grid.py, node_list.py | 已删除，更新为实际结构 |
| 架构描述 | 无 | 新增完整分层说明 |
| 页面功能 | 简略 | 5 页面详细功能表 |
| GUI 文件 | 5 个 | 21 个 widgets + 5 个 pages |

---

## 六、最终文档结构

```
docs/
├── README.md                          # 文档入口
├── host.md                            # ⭐ 已更新 (v5.2 目录树)
├── architecture.md                    # 架构说明
├── agent.md                           # Agent 说明
├── protocol.md                        # 通信协议
├── api.md                             # API 文档
├── events.md                          # 事件系统
├── configuration.md                   # 配置说明
├── collectors.md                      # 采集器
├── database.md                        # 数据库
├── development.md                     # 开发指南
├── installation.md                    # 安装指南
├── changelog.md                       # 变更日志
├── RUN_REPORT.md                      # 运行报告
│
├── design/
│   └── ui_design_system.md            # ⭐ 唯一权威 UI 设计规范
│
├── phases/
│   ├── phase_3_3a_design.md           # ✅ Status: COMPLETE
│   ├── phase_3_3c_detail_panel_design.md  # ✅ Status: COMPLETE
│   ├── phase_3_4_alerts_design.md     # ✅ Status: COMPLETE
│   ├── phase_3_5_monitor_design.md    # ✅ Status: COMPLETE
│   ├── phase_3_6_settings_design.md   # ✅ Status: COMPLETE
│   ├── phase_3_7_widget_migration.md  # ✅ Status: 完成
│   ├── phase_3_8_main_window_refactor.md  # ✅ Status: 完成
│   └── phase_3_9_theme_audit.md       # ✅ Status: COMPLETE
│
├── archive/
│   ├── ui_design_v50.md               # 归档: v5.0 UI 设计
│   ├── unified_ui_design.md           # 归档: 统一 UI 设计
│   ├── v52_ui_design_legacy.md        # 归档: v5.2 旧 UI 设计
│   ├── v52_structure_audit.md         # 归档: 结构审计
│   ├── v52_architecture_review.md     # 归档: 架构评审
│   └── v52_phase25_scan.md            # 归档: Phase 2.5 扫描
│
└── phase_4_5_audit_report.md          # Phase 4-5 审计报告
```

---

## 七、保留 vs 删除 vs 归档

### 保留 (20 个)

根目录 14 个核心文档 + design/ 1 个 + phases/ 8 个 + audit 1 个

### 归档 (6 个)

全部移入 `docs/archive/`，不删除：

| 文件 | 原因 |
|------|------|
| `ui_design_v50.md` | v5.0 设计，已被 v5.2 取代 |
| `unified_ui_design.md` | 与 spec 重叠，颜色冲突 |
| `v52_ui_design_legacy.md` | 路径/模块名过期 |
| `v52_structure_audit.md` | 历史快照，路径过期 |
| `v52_architecture_review.md` | 历史评审 |
| `v52_phase25_scan.md` | 历史扫描 |

### 删除 (0 个)

**零删除**。所有文档保留或归档，不丢失任何历史信息。

---

## 八、遗留问题（非本次范围）

| 问题 | 优先级 | 说明 |
|------|--------|------|
| 硬编码颜色 25 处 | P1 | 需在 RC-3 阶段修复 |
| common/theme.py 残留引用 8 处 | P1 | 需迁移到 host.gui.theme |
| card_widget.py 可删除 | P2 | 仅 __init__ 导出，未被使用 |
| navigation_controller legacy 参数 | P2 | 可清理 |
| 测试文件命名不统一 | P3 | test_v52_* vs test_phase_* |
