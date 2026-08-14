# Phase 5-3 History Query API Plan

> **Status**: DRAFT (待冻结)
> **Scope**: 历史指标读取能力，不含 UI / Chart / Retention
> **原则**: 单向依赖 Storage → Facade → (VM)，查询逻辑留在 Repository

---

## 1. 目标

在 Phase 5-1/5-2 已建的存储与写入基础之上，提供历史指标读取 API。

```
HistoryVM (暂不建，留给 5-4)
    ↓
HistoryFacade (新增)
    ↓
MetricsRepository (扩展 latest)
    ↓
SQLite
```

**不含**：UI / Chart / Export / Retention / Migration / downsample

---

## 2. 当前事实核对

### 已存在 (Phase 5-1)

MetricsRepository 已具备：

| 方法 | 状态 |
|------|------|
| `query_range(node_id, metric, start, end, limit)` | ✅ 已实现 |
| `aggregate(node_id, metric, start, end)` → {avg,min,max,count} | ✅ 已实现 |
| `count(node_id?, metric?)` | ✅ 已实现 |
| `nodes()` / `metrics(node_id)` | ✅ 已实现 |
| `insert` / `insert_batch` | ✅ 已实现 (5-2 使用) |

### 缺失

| 项 | 说明 |
|----|------|
| `latest()` 查询 | 最近 N 条，需新增 |
| HistoryFacade | 不存在，需新增 |
| HistoryVM | 不存在（5-3 不建） |

---

## 3. 核心 API 范围

### 3.1 Range Query（已存在，验收即可）

```python
query_range(node_id, metric, start_time, end_time, limit) -> list[MetricRecord]
```

### 3.2 Latest Query（新增）

```python
latest(node_id, metric, limit=300) -> list[MetricRecord]
```

- 用途：History UI 初始加载 / 快速恢复最近状态
- 语义：按时间倒序返回最近 N 条
- **排序保证**：Repository 层 `ORDER BY timestamp DESC`，调用方直接得到 newest → oldest，无需二次排序

### 3.3 Aggregation（已存在，验收即可）

```python
aggregate(node_id, metric, start, end) -> {"avg", "min", "max", "count"}
```

第一版仅 avg/min/max/count，不做 percentile / stddev。

---

## 4. 新增文件结构

```
host/
 ├── facade/
 │    └── history_facade.py       # 新增：封装 repository 的读取接口
 │
 ├── storage/
 │    └── repositories/
 │         └── metrics_repo.py    # 扩展：新增 latest()
 │
 └── viewmodels/
      └── history_vm.py           # 不建，留给 5-4
```

### HistoryFacade 职责

| 做 | 不做 |
|----|------|
| 封装 range/latest/aggregate 三个读取接口 | UI 数据转换 |
| 转发 repository 结果 | Chart 格式化 |
| 参数校验（node_id/metric 非空） | retention |

**错误语义**：
- 非法查询参数（node_id/metric 为空）→ `raise ValueError`
- 数据不存在（合法参数但无记录）→ 返回 `[]`（empty list）

```python
class HistoryFacade:
    def __init__(self, metrics_repo): ...

    def query_range(self, node_id, metric, start, end, limit=1000) -> list[MetricRecord]:
        return self._repo.query_range(node_id, metric, start, end, limit)

    def latest(self, node_id, metric, limit=300) -> list[MetricRecord]:
        return self._repo.latest(node_id, metric, limit)

    def aggregate(self, node_id, metric, start, end) -> dict:
        return self._repo.aggregate(node_id, metric, start, end)
```

---

## 5. 明确禁止

| 禁止 | 属于 |
|------|------|
| ChartPoint / SeriesData | Phase 5-4 |
| last hour / today / 7 days 时间窗口 | UI/业务层 |
| downsample（10000→500） | 图表性能优化 |
| delete old data / compress / archive | Phase 5-5 |
| schema migration | 未来 schema v2 时 |

Repository 只接受 `start_time` / `end_time`，不做时间窗口语义。

---

## 6. 测试门禁

新增 `tests/test_v52_history_query.py`：

| Case | 验证 |
|------|------|
| range query | 写入 t1/t2/t3，查 t1~t2 → 2 records |
| latest | 插入 100，limit 10 → 10 records，时间倒序 |
| aggregation | avg/min/max/count 正确 |
| node isolation | node_A / node_B 查询不串数据 |
| empty result | 不存在 node → []，非异常 |

---

## 7. Phase 5-3 验收标准

| 项目 | 目标 |
|------|------|
| latest() 实现 | ✅ |
| HistoryFacade 存在 | ✅ |
| range/latest/aggregate 通过 | ✅ |
| 查询逻辑留在 Repository | ✅ |
| UI / Chart / retention 未引入 | ✅ |
| sqlite 仅在 storage/ | ✅ |
| tests pass | ✅ |
| full regression | ✅ |

---

## 8. 不做事项

| 不做 | 留给 |
|------|------|
| HistoryUI | Phase 5-4 |
| Chart 数据格式 | Phase 5-4 |
| downsample | Phase 5-4 |
| retention | Phase 5-5 |
| HistoryVM | Phase 5-4 |
| migration | schema v2 时 |
