# Phase 5-3 History Query API Report

> **Generated**: 2026-08-13
> **Status**: COMPLETE
> **Scope**: 历史指标读取 API，不含 UI / Chart / Retention

---

## 一、执行摘要

| 维度 | 结果 |
|------|------|
| latest() 实现 | ✅ ORDER BY timestamp DESC |
| HistoryFacade 新增 | ✅ range/latest/aggregate |
| 查询逻辑留在 Repository | ✅ |
| UI / Chart / retention 未引入 | ✅ |
| 错误语义 | ✅ ValueError / [] |
| tests | ✅ 23/23 |
| full regression | ✅ 881/881 PASS |

---

## 二、变更清单

| 文件 | 变更 |
|------|------|
| `host/storage/repositories/metrics_repo.py` | 扩展：新增 `latest()` |
| `host/facade/history_facade.py` | 新增：读取门面 |
| `tests/test_v52_history_query.py` | 新增：23 项测试 |

---

## 三、API

### MetricsRepository.latest

```python
latest(node_id, metric, limit=300) -> list[MetricRecord]
# ORDER BY timestamp DESC，newest → oldest
```

### HistoryFacade

| 方法 | 语义 |
|------|------|
| `query_range(node_id, metric, start, end, limit)` | 升序，区间查询 |
| `latest(node_id, metric, limit)` | 倒序，最近 N 条 |
| `aggregate(node_id, metric, start, end)` | avg/min/max/count |

**错误语义**：
- 非法参数（node_id/metric 为空）→ `ValueError`
- 数据不存在 → `[]` / `count=0`

---

## 四、数据流

```
HistoryFacade
    ↓
MetricsRepository (latest / query_range / aggregate)
    ↓
SQLite
```

查询逻辑完全留在 Repository 层，Facade 只做参数校验和转发。

---

## 五、测试结果

```
test_v52_history_query:  23/23 PASS (新增)
全量测试:                881/881 PASS
```

| Case | 结果 |
|------|------|
| range query | ✅ 区间 + 边界 + 空重叠 |
| latest | ✅ limit + 倒序 + 最新值 |
| aggregation | ✅ avg/min/max/count |
| node isolation | ✅ A/B 不串数据 |
| empty result | ✅ [] 非异常 |
| 错误语义 | ✅ ValueError |
| 架构边界 | ✅ 无 gui/sqlite3/PyQt5 |

---

## 六、Phase 5 进度

```
5-1 Storage Foundation      ✅
5-2 Metrics Persistence     ✅
5-3 History Query API       ✅
5-4 History UI              Future
5-5 Retention / Cleanup     Future
```
