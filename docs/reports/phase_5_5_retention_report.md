# Phase 5-5A Retention Foundation Report

> **Generated**: 2026-08-13
> **Status**: COMPLETE
> **Scope**: 数据保留策略 + 清理服务基础，不含 UI / 定时器 / 后台线程

---

## 一、执行摘要

| 维度 | 结果 |
|------|------|
| RetentionPolicy 存在 | ✅ |
| 三 repo delete_before | ✅ |
| RetentionService 存在 | ✅ |
| storage layer only | ✅ |
| 无 UI / 线程依赖 | ✅ |
| sqlite 仅 storage/ | ✅ |
| tests | ✅ 14/14 |
| full regression | ✅ 915/915 PASS |

---

## 二、变更清单

| 文件 | 变更 |
|------|------|
| `host/storage/retention.py` | 新增：RetentionPolicy + RetentionService |
| `host/storage/repositories/metrics_repo.py` | 扩展：`delete_before()` |
| `host/storage/repositories/alerts_repo.py` | 扩展：`delete_before()` |
| `host/storage/repositories/sessions_repo.py` | 扩展：`delete_before()` |
| `tests/test_v52_retention.py` | 新增：14 项测试 |

---

## 三、API

### RetentionPolicy

```python
@dataclass
class RetentionPolicy:
    metrics_days: int = 30
    alerts_days: int = 90
    sessions_days: int = 90
```

### RetentionService

```python
svc.run(now=None) -> {"metrics": n, "alerts": n, "sessions": n}
```

### Repository.delete_before

```python
delete_before(timestamp) -> int  # 删除 timestamp < 阈值，返回删除数量
```

**边界语义**：严格小于（`<`），`timestamp == cutoff` 保留。

---

## 四、架构规则落实

| 规则 | 验证 |
|------|------|
| 删除走 Repository | ✅ retention.py 无 DELETE SQL，调用 delete_before |
| Record 模型不变 | ✅ |
| 无后台线程 | ✅ 无 QTimer/QThread |
| 可测试 | ✅ 边界/空表/临界 覆盖 |
| 不改 schema | ✅ 用现有 REAL timestamp |

---

## 五、测试结果

```
test_v52_retention:  14/14 PASS (新增)
全量测试:            915/915 PASS
```

| Case | 结果 |
|------|------|
| delete_before 100→50 | ✅ |
| 临界时间（< 而非 <=） | ✅ |
| RetentionService.run 计数 | ✅ |
| 空表返回 0 | ✅ |
| 架构边界 | ✅ |

---

## 六、Phase 5 进度

```
5-1 Storage Foundation    ✅
5-2 Metrics Persistence   ✅
5-3 History Query API     ✅
5-4 History UI            ✅
5-5 Retention (5-5A)      ✅ 基础完成
    ├── 5-5B Cleanup Integration  Future (startup 触发)
    └── 5-5C Settings Integration  Future
```
