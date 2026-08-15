# Project Cleanup Execution Plan

> **Status**: FROZEN
> **性质**: 发布前工程整理，不修改业务逻辑/不重构大模块/不添加新功能
> **执行顺序**: 本地清理先行，最后 git push

---

## 执行顺序

| Step | 任务 | 类型 |
|------|------|------|
| 1 | service 目录统一（services → service） | 命名修复 |
| 2 | MetricPersistenceService 接入 DataController | 数据流闭环 |
| 3 | SummaryCard 治理（不破坏 UI） | 去重 |
| 4 | gitignore *.db | 仓库卫生 |
| 5 | 文档同步（ARCHITECTURE/ROADMAP/DEVELOPMENT） | 文档债 |
| 6 | git commit + push + tag v5.2.3 | 发布 |

---

## Step 1: service 目录统一

```
host/services/metric_persistence.py → host/service/metric_persistence.py
删除 host/services/
```

- 更新 logger 名称 `host.services.*` → `host.service.*`
- 更新 `tests/test_metric_persistence.py` import + 源码扫描路径
- 验收：`host/services` 不存在，grep `services` 0 运行时引用

## Step 2: MetricPersistence 接入

DataController._on_data 内新增 persist_frame 调用（与 FrameStore/HistoryStore 同级）。

- 保持 Collector / MonitorFrame / Runtime Model 不变
- 验收：新增 test_metric_persistence_flow.py，验证 frame → DataController → Service → Repository → record

## Step 3: SummaryCard 治理

两个接口不同（dashboard: value+28px；chart_panel: sub+20px），不简单删除。

方案：统一 SummaryCard 接口（title, value, subtitle=None, size），或抽象基类。

## Step 4: gitignore

加入 `*.db` / `*.sqlite` / `*.sqlite3`，不提交 history.db。

## Step 5: 文档同步

- ARCHITECTURE.md 补 storage/ + history 组件
- ROADMAP.md 反映 Phase 5 完成
- DEVELOPMENT.md 补 Storage 层规范

## Step 6: git commit + push + tag

commit message: `v5.2.3: project cleanup - persistence wiring, service dir, docs sync`
tag: v5.2.3
push: commit + tags

---

## 最终目标状态

```
v5.2.3-cleanup
├── Architecture      ✅
├── Storage Pipeline  ✅
├── Persistence       ✅ (real active)
├── History           ✅
├── Retention         ✅
├── Theme             ✅
├── Tests             ✅
├── GitHub Sync       ✅
└── Documentation     ✅
```
