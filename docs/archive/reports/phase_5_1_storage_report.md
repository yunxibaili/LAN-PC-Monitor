# Phase 5-1 Storage Foundation Report

> **Generated**: 2026-08-13
> **Status**: COMPLETE
> **Scope**: Storage 层基础建设，不涉及 UI

---

## 一、执行摘要

| 维度 | 结果 |
|------|------|
| host/storage/ created | ✅ 6 文件 |
| SQLite schema versioned | ✅ v1 |
| Repository layer | ✅ 3 repos |
| Runtime models unchanged | ✅ |
| UI no storage dependency | ✅ |
| storage tests pass | ✅ 33/33 |
| full regression | ✅ 836/836 PASS |

---

## 二、新增文件

```
host/storage/
 ├── __init__.py
 ├── database.py           # SQLite connection + lifecycle
 ├── schema.py             # Table definitions + version
 ├── records.py            # Record dataclasses
 └── repositories/
      ├── __init__.py
      ├── metrics_repo.py   # 指标历史读写
      ├── alerts_repo.py    # 告警历史读写
      └── sessions_repo.py  # 会话快照读写
```

---

## 三、Database 设计

| 特性 | 实现 |
|------|------|
| 连接 | `sqlite3.connect()` + WAL mode |
| Schema | `init_schema()` 自动建表 |
| 版本 | `schema_version` 表，当前 v1 |
| Transaction | `commit()` 显式提交 |
| Context manager | `with Database(path) as db:` |
| 测试 | `:memory:` 内存数据库 |

---

## 四、Schema (v1)

| 表 | 字段 |
|----|------|
| `metrics` | id, node_id, metric, value, timestamp |
| `alerts` | id, node_id, node_alias, name, path, value, threshold, level, timestamp |
| `sessions` | id, node_id, snapshot (JSON), timestamp |
| `schema_version` | version, applied_at |

索引：metrics(node_id, timestamp), alerts(node_id, timestamp), sessions(node_id, timestamp)

---

## 五、Repository 接口

### MetricsRepository

| 方法 | 签名 |
|------|------|
| `insert` | `(MetricRecord) → None` |
| `insert_batch` | `(list[MetricRecord]) → None` |
| `query_range` | `(node_id, metric, start, end, limit) → list[MetricRecord]` |
| `count` | `(node_id?, metric?) → int` |
| `aggregate` | `(node_id, metric, start, end) → dict{avg,min,max,count}` |
| `nodes` | `() → list[str]` |
| `metrics` | `(node_id) → list[str]` |
| `clear` | `(node_id?) → None` |

### AlertsRepository

| 方法 | 签名 |
|------|------|
| `insert` | `(AlertHistoryRecord) → None` |
| `query_recent` | `(limit) → list[AlertHistoryRecord]` |
| `query_by_level` | `(level, limit) → list[AlertHistoryRecord]` |
| `query_by_node` | `(node_id, limit) → list[AlertHistoryRecord]` |
| `count` | `(level?) → int` |
| `clear` | `() → None` |

### SessionsRepository

| 方法 | 签名 |
|------|------|
| `create` | `(SessionRecord) → None` |
| `query_recent` | `(node_id?, limit) → list[SessionRecord]` |
| `count` | `(node_id?) → int` |
| `clear` | `(node_id?) → None` |

---

## 六、测试结果

```
test_v52_storage:  33/33 PASS (新增)
全量测试:         836/836 PASS
```

---

## 七、架构验证

| 检查 | 结果 |
|------|------|
| storage → gui import | ✅ 0 处 |
| viewmodels → sqlite3 | ✅ 0 处 |
| Record 与 Runtime 分离 | ✅ |
| Repository 不依赖 host/gui | ✅ |
