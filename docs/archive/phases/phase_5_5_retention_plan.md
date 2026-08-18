# Phase 5-5 Retention Plan

> **Status**: DRAFT (待冻结)
> **Scope**: 数据保留策略 + 自动清理基础，不含 UI / 定时器 / 后台线程
> **原则**: Storage 删除只能走 Repository，不修改 schema / Runtime Model

---

## 1. 目标

```
Collector
    ↓
PersistenceService
    ↓
Storage
    ↓
RetentionService   ← 新增
    ↓
SQLite (DELETE FROM ... WHERE timestamp < ?)
```

解决 metrics 无限增长问题：`recent data + controlled cleanup`。

---

## 2. 当前事实核对

### 已存在

| 项 | 状态 |
|----|------|
| metrics/alerts/sessions 表 timestamp | ✅ `REAL NOT NULL` (Unix timestamp) |
| MetricRecord.timestamp | ✅ float (Unix timestamp) |
| Repository clear() | ✅ 全删/按节点删 |
| Repository delete_before() | ❌ 不存在，需新增 |
| RetentionPolicy / RetentionService | ❌ 不存在 |

### 时间字段（冻结）

- metrics 表 `timestamp REAL` = Unix 秒级时间戳
- Retention SQL 与现有 schema 完全一致，**不改 schema**

---

## 3. 拆分

### 5-5A Retention Foundation（本阶段）

新增：

```
host/storage/retention.py
```

| 组件 | 职责 |
|------|------|
| `RetentionPolicy` | 数据类：metrics_days=30, alerts_days=90, sessions_days=90 |
| `RetentionService` | 调用 repository 的 delete_before() |

Repository 扩展：

```python
# MetricsRepository / AlertsRepository / SessionsRepository 各新增
def delete_before(self, before: float) -> int:
    """删除 timestamp < before 的记录，返回删除数量。"""
```

### 5-5B Cleanup Integration（后续）

- Application startup 时执行一次 retention check
- 不轮询、不后台线程

### 5-5C Settings Integration（后续，不进入本阶段）

- Settings 里的 Retention 配置（天/容量），避免污染已完成的 Settings

---

## 4. 架构规则（冻结）

### 规则 1: 删除只能走 Repository

**禁止**：
```python
# ❌ RetentionService 直接执行 SQL
self._db.execute("DELETE FROM metrics WHERE timestamp < ?", ...)
```

**必须**：
```python
# ✅ 走 Repository
self._metrics_repo.delete_before(before)
```

### 规则 2: 不修改 Record 模型

`MetricRecord` / `AlertHistoryRecord` / `SessionRecord` 不变。

### 规则 3: 不引入后台线程

**禁止**：QTimer 轮询 / QThread / `while True: cleanup()`

5-5A 只提供手动调用能力，触发点在 5-5B（startup）。

### 规则 4: 删除可测试

```
insert 100 → cleanup(before T) → remaining == 50
```

---

## 5. RetentionService 设计

```python
class RetentionPolicy:
    def __init__(self, metrics_days=30, alerts_days=90, sessions_days=90):
        ...

    def cutoff(self, days: int, now: float = None) -> float:
        """返回删除阈值（Unix 时间戳）。"""
        ...


class RetentionService:
    def __init__(self, policy, metrics_repo, alerts_repo, sessions_repo):
        ...

    def run(self, now: float = None) -> dict:
        """执行清理，返回各表删除数量。"""
        return {
            "metrics": self._metrics_repo.delete_before(self._policy.cutoff(self._policy.metrics_days)),
            "alerts": self._alerts_repo.delete_before(...),
            "sessions": self._sessions_repo.delete_before(...),
        }
```

---

## 6. 第一版不做

| 不做 | 属于 |
|------|------|
| VACUUM / partition / archive | 后续优化 |
| compression | 后续 |
| 自动定时清理 | 5-5B |
| UI 设置 | 5-5C |
| 容量阈值（512MB） | 后续 |

第一版只用 `DELETE FROM metrics WHERE timestamp < ?`。

---

## 7. 测试门禁

新增 `tests/test_v52_retention.py`：

| Case | 验证 |
|------|------|
| delete_before | insert 100 → delete before T → remaining == 50 |
| 边界 | timestamp == before 不删除（仅 < before） |
| RetentionService.run | 返回 {metrics, alerts, sessions} 计数 |
| 空表 | delete_before 返回 0 |
| 架构 | RetentionService 不 import sqlite3 |

---

## 8. 验收标准

| 项目 | 目标 |
|------|------|
| RetentionPolicy 存在 | ✅ |
| Repository delete API | ✅ 三表 |
| RetentionService 存在 | ✅ |
| storage layer only | ✅ |
| 无 UI 依赖 | ✅ |
| sqlite 仅 storage/ | ✅ |
| cleanup tests | ✅ |
| full regression | ✅ |

---

## 9. 不做事项

| 不做 | 留给 |
|------|------|
| 自动清理触发 | 5-5B |
| Settings Retention UI | 5-5C |
| VACUUM / archive | 后续 |
| schema 变更 | 不做 |
