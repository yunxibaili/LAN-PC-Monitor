# 整体代码审查报告

> **生成**: 2026-08-13
> **性质**: 只读审查，未修改任何代码
> **依据**: docs/core/BLUEPRINT.md + ARCHITECTURE.md + 各 RC/Phase 报告

---

## 一、审查结论摘要

| 维度 | 结果 | 说明 |
|------|------|------|
| 架构分层 | ✅ PASS | Page/Widget/VM 边界干净 |
| 依赖方向 | ✅ PASS | common→host = 0 |
| Theme | ✅ PASS | 硬编码颜色 = 0，token 已收口 |
| Storage 隔离 | ✅ PASS | sqlite3 仅在 storage/ |
| 文档一致性 | ❌ FAIL | BLUEPRINT.md 严重过期 |
| Git 卫生 | ⚠️ 待处理 | RC-7 之后成果未提交 |

---

## 二、架构分层检查（全通过）

### Page 层

```
Page → Store / ConfigManager / sqlite3: 0 处 ✅
```

### Widget 层

```
Widget → Store / ViewModels: 0 处 ✅
```

### ViewModel 层

```
ViewModel → PyQt5: 0 处 ✅
```

> 注：扫描曾标记 `monitor_vm.py` 含 "QTimer"，核实为 docstring 中「禁止」清单的第 8 行，非真实 import，属误报。

### common → host

```
0 处 ✅
```

---

## 三、Theme 检查

| 项 | 结果 |
|----|------|
| host/gui 非 theme 区硬编码颜色 | 0 处 ✅ |
| token 单一来源 (common/theme_tokens.py) | ✅ 已接线 |
| common/theme.py legacy 标记 | ✅ RC-7B 已加 |

---

## 四、Storage 隔离检查

| 项 | 结果 |
|----|------|
| sqlite3 使用位置 | 仅 host/storage/database.py ✅ |
| UI 无 storage 依赖 | ✅ |
| Runtime/Storage model 分离 | ✅ (MetricRecord 独立) |

---

## 五、文档与代码不一致（主要问题）

BLUEPRINT.md 停留在 Phase 4-6 状态，代码已推进到 Phase 5-2。逐项核对：

| # | BLUEPRINT 描述 | 代码实际 | 偏差 |
|---|----------------|----------|------|
| 1 | Status: Settings Redesign in progress (L5) | Phase 5-2 已完成 | ❌ |
| 2 | Settings 🔄 进行中 (L44) | 已完成 (4-6A/B/C) | ❌ |
| 3 | Tests 724+ (L46) | 858 | ❌ |
| 4 | SQLite = Future (L113) | 已引入 (Phase 5-1) | ❌ |
| 5 | theme_tokens 未接线 (L398-406) | RC-7 已接线 | ❌ |
| 6 | Phase 5 历史数据 = Future (L72) | 5-1/5-2 已完成 | ❌ |
| 7 | 技术债 #1 Theme 收口 P1 (L520) | 已解决 | ❌ |
| 8 | 技术债 #2 Settings P1 (L521) | 已解决 | ❌ |
| 9 | 技术债 #5 历史数据缺失 P2 (L525) | 已建 Storage 层 | ❌ |
| 10 | 目录缺 host/storage/、host/services/metric_persistence.py | 已存在 | ❌ |
| 11 | 测试数 724/783 (L504-507) | 858 | ❌ |

**根因**：RC-7、Phase 4-6、Phase 5 完成后未回写 BLUEPRINT。

---

## 六、代码架构真实状态（与 BLUEPRINT 目标一致）

```
代码实际已实现 BLUEPRINT 第 4 章描述的目标架构：

Agent Collector
  ↓ WebSocket
Host DataController
  ├── FrameStore / HistoryStore / NodeStore / AlertStore
  ├── AlertService
  └── MetricPersistenceService (Phase 5-2, 文档未记录)
        ↓
     MetricsRepository (Phase 5-1, 文档未记录)
        ↓
     SQLite (host/storage/)
```

架构本身健康，只是文档滞后。

---

## 七、Git 卫生

`v5.2-rc1` (d116e6b) 之后有大量未提交变更：

| 类型 | 数量 | 归属 |
|------|------|------|
| Modified | 16 | Phase 4-6 + RC-7 修改 |
| Untracked | 35+ | RC-7 + Phase 5 新文件 |

**建议**：Phase 5-2 完成后应打 `v5.2-rc2` 或 `v5.2-phase5-1` 标签，避免后续回滚困难。

---

## 八、遗留问题清单（更新后）

| # | 问题 | 优先级 | 状态 |
|---|------|--------|------|
| 1 | BLUEPRINT.md 过期 | P1 | 需回写 Phase 4-6/RC-7/Phase 5 状态 |
| 2 | common/theme.py 迁移 | P2 | 留给 Phase 4-7 Agent GUI |
| 3 | common/protocol.py 遗留 | P2 | v4 TCP 残留 |
| 4 | common/gui/detail_panel.py 重复 | P2 | Agent 自包含版本 |
| 5 | i18n 未统一 | P3 | |
| 6 | Agent GUI 未升级 | P3 | Phase 4-7 |
| 7 | git 未提交 | P1 | 打基线标签 |

---

## 九、结论

1. **代码架构健康**：分层、依赖方向、Theme、Storage 隔离全部达标，符合 BLUEPRINT 第 4 章目标。
2. **主要风险是文档漂移**：BLUEPRINT.md 有 11 处与实际不符，会误导后续开发。
3. **建议下一步**（按优先级）：
   - P0: 回写 BLUEPRINT.md（反映 Phase 4-6/RC-7/Phase 5 完成状态）
   - P0: git 提交 + 打基线标签
   - P1: 继续 Phase 5-3 History Query API
