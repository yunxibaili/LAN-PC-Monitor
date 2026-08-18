# Phase 5-2 Metrics Persistence Plan

> **Status**: DRAFT (待冻结)
> **Scope**: Collector → Storage 写入管线，不涉及 UI / 查询 / 图表
> **原则**: Batch 写入，单帧单 transaction，不污染 Runtime Model

---

## 1. 目标

将 Collector 采集的指标数据持久化到 SQLite：

```
Collector (每秒)
    │
    ▼
MetricPersistenceService  ← 新增
    │
    ▼
MetricsRepository.insert_batch()
    │
    ▼
SQLite
```

**不提前做**：History UI / 查询 API / 图表 / retention / Runtime Model 改造

---

## 2. 当前架构事实

### Collector → Runtime (现有)

```
Collector.collect() → dict
    ↓
Aggregator组装 monitor_data 帧
    ↓
DataController._on_data()
    ├── FrameStore.push()         → Runtime (最新帧)
    ├── HistoryStore.push()       → Runtime (内存 deque)
    ├── NodeStore.update_status() → Runtime (状态)
    └── AlertService._on_frame()  → Runtime (告警检测)
```

### Storage 层 (Phase 5-1 已建)

```
host/storage/
 ├── database.py          # SQLite 连接
 ├── schema.py            # 表定义 (metrics / alerts / sessions)
 ├── records.py           # MetricRecord / AlertHistoryRecord / SessionRecord
 └── repositories/
      ├── metrics_repo.py
      ├── alerts_repo.py
      └── sessions_repo.py
```

### 缺失

| 缺失 | 说明 |
|------|------|
| Persistence Service | 无 Collector → Storage 管线 |
| Batch 写入 | 无 frame → records 转换 |
| 接线位置 | DataController 不知道 Storage |

---

## 3. 技术约束

### 约束 1: Batch 写入

**禁止**：

```python
for metric in metrics:
    repo.insert(metric)    # N 次 commit
```

**必须**：

```python
records = convert_frame(node_id, frame)
repo.insert_batch(records)  # 1 次 commit
```

### 约束 2: Runtime / Storage 分离

**禁止**：

```python
MonitorFrame.to_sql()
MetricCollector import host.storage
```

**推荐**：

```
Collector
    │
Persistence Adapter (转换层)
    │
Repository
    │
SQLite
```

### 约束 3: 单帧单 Transaction

每帧数据 → 一次 batch insert → 一次 commit

---

## 4. 新增模块

```
host/
 └── services/
      └── metric_persistence.py   # Persistence Service
```

### MetricPersistenceService 职责

| 做 | 不做 |
|----|------|
| 接收 runtime frame | UI 数据转换 |
| 转换为 MetricRecord 列表 | 查询 / 聚合 |
| batch 写入 repository | 图表渲染 |
| 处理写入失败 | retention 清理 |

### 接口设计

```python
class MetricPersistenceService:
    def __init__(self, metrics_repo: MetricsRepository):
        self._repo = metrics_repo

    def persist_frame(self, node_id: str, frame: dict) -> None:
        """将一帧 monitor_data 转换并持久化。"""
        records = self._convert(node_id, frame)
        if records:
            self._repo.insert_batch(records)

    def _convert(self, node_id: str, frame: dict) -> list[MetricRecord]:
        """帧 → MetricRecord 列表。"""
        ...
```

### 帧 → Record 转换映射

| 帧字段 | Metric 名 | 值字段 |
|--------|-----------|--------|
| cpu.total_usage | cpu.usage | total_usage |
| cpu.package_temp_c | cpu.temp | package_temp_c |
| gpu.usage_percent | gpu.usage | usage_percent |
| gpu.core_temp_c | gpu.temp | core_temp_c |
| ram.usage_percent | ram.usage | usage_percent |
| net.upload_mb_s | net.upload | upload_mb_s |
| net.download_mb_s | net.download | download_mb_s |
| net_quality.quality_score | net.score | quality_score |
| fps.fps | fps.value | fps |
| fps.frame_time_ms | fps.frame_time | frame_time_ms |

---

## 5. 接线位置

### 方案：DataController 注入

```
MainWindow
    │
    ├── DataController
    │    │
    │    ├── FrameStore
    │    ├── HistoryStore
    │    ├── NodeStore
    │    └── MetricPersistenceService  ← 新增注入
    │
    └── MetricPersistenceService
         │
         └── MetricsRepository (Phase 5-1)
```

DataController._on_data() 中新增一行：

```python
self._persistence.persist_frame(node_id, frame)
```

---

## 6. 测试策略

### 新增

```
tests/test_metric_persistence.py
```

### Case

| Case | 验证 |
|------|------|
| frame → records 转换 | 字段映射正确，None 值跳过 |
| batch insert | insert_batch 调用一次 |
| 多节点聚合 | 不同 node_id 不混淆 |
| 写入失败不崩溃 | 异常捕获，Runtime 不受影响 |
| 依赖方向 | persistence → storage = 0 |

---

## 7. Phase 5-2 验收标准

| 项目 | 目标 |
|------|------|
| metric_persistence.py exists | ✅ |
| Collector interface unchanged | ✅ |
| MonitorFrame unchanged | ✅ |
| Repository batch used | ✅ |
| single frame → single transaction | ✅ |
| storage/gui dependency = 0 | ✅ |
| sqlite access outside storage = 0 | ✅ |
| tests pass | ✅ |
| full regression | ✅ |

---

## 8. 不做事项

| 不做 | 留给 |
|------|------|
| History UI | Phase 5-4 |
| 查询 API | Phase 5-3 |
| 图表 | Phase 5-4 |
| retention 清理 | Phase 5-5 |
| Runtime Model 改造 | 不做 |
| Collector 接口变更 | 不做 |
