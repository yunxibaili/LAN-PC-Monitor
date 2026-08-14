# Phase 5 Storage Foundation Plan

> **Status**: DRAFT (待冻结)
> **Scope**: Storage 层基础建设，不涉及 UI
> **原则**: Collector → Service → Storage → VM → UI，禁止反向依赖

---

## 1. 背景与目标

### 背景

v5.2 Stabilization 已完成。当前运行数据全部存在于内存模型中：

| Store | 存储方式 | 容量 | 生命周期 |
|-------|----------|------|----------|
| FrameStore | dict (node_id → frame) | 每节点 1 帧 | 运行时 |
| HistoryStore | deque (maxlen=300) | 每指标 300 点 (~5min) | 运行时 |
| AlertStore | list (30s 去重) | 最近告警 | 运行时 |
| NodeStore | dict (元数据/状态) | 所有节点 | 运行时 |

**缺失能力**：
- 无历史查询（进程重启后数据丢失）
- 无趋势分析（只有 5 分钟窗口）
- 无报表生成
- 无数据保留策略

### 目标

```
Runtime Monitoring
        │
        v
Storage Persistence (Phase 5)
        │
        v
History Query API
        │
        v
Visualization / Reports
```

---

## 2. 当前架构事实核对

### 已存在

| 模块 | 职责 | 位置 |
|------|------|------|
| ConfigManager | JSON 配置读写 | common/config.py |
| SettingsFacade | 配置统一入口 | host/facade/settings_facade.py |
| AlertEngine | 红线告警检测 | host/alerts.py |
| AlertStore | 告警记录 (内存) | host/store/alert_store.py |
| HistoryStore | 历史趋势 (内存 deque) | host/store/history_store.py |
| FrameStore | 最新帧缓存 (内存) | host/store/frame_store.py |

### 不存在

| 模块 | 说明 |
|------|------|
| host/storage/ | 不存在 |
| SQLite 依赖 | 无任何 sqlite3 import |
| Repository 层 | 不存在 |
| History API | 不存在 |
| Metrics retention | 不存在 |
| Schema migration | 不存在 |

### Collector 输出结构 (10 个)

```
cpu_collector.py      → cpu.total_usage, cpu.package_temp_c, ...
gpu_collector.py      → gpu.usage_percent, gpu.core_temp_c, ...
ram_collector.py      → ram.usage_percent, ram.total_gb, ...
disk_collector.py     → disk[].read/write_mb_s, disk[].usage
net_collector.py      → net.upload/download_mb_s
net_quality_collector.py → net_quality.quality_score
fps_collector.py      → fps.fps, fps.frame_time_ms
proc_collector.py     → processes.top_cpu, processes.top_gpu
sys_collector.py      → system.hostname, system.local_ip
base.py               → BaseCollector 基类
```

### NodeDetailData 完整字段

```
IdentityData:  node_id, alias, status, ip, port
SystemData:    hostname, local_ip, uptime
CpuData:       name, usage, cores_phys, cores_logic, freq_mhz, temp_c, power_w
MemoryData:    total_gb, used_gb, avail_gb, usage, swap_mb
GpuData:       name, usage, vram_used, vram_total, core_temp, hotspot_temp, freq_mhz, power_w
DiskData:      drive, read_mb_s, write_mb_s, usage, free_gb, all_disks
NetworkData:   iface, up_mb_s, down_mb_s, link_speed
QualityData:   rtt, gw_rtt, loss, score, grade
FpsData:       window, value, frame_time, low1, source
ProcessData:   cpu_text, gpu_text
```

---

## 3. Storage 架构目标

### 目标目录结构

```
host/
 └── storage/
      ├── __init__.py
      ├── database.py          # SQLite connection + lifecycle
      ├── schema.py            # Table definitions + migration
      └── repositories/
           ├── __init__.py
           ├── metrics_repo.py     # 指标历史读写
           ├── alerts_repo.py      # 告警历史读写
           └── sessions_repo.py    # 会话/快照记录
```

### 各模块职责

| 模块 | 职责 | 不负责 |
|------|------|--------|
| database.py | SQLite connection, lifecycle, transaction | 业务查询, UI 数据转换 |
| schema.py | Table definition, migration version | 数据读写 |
| MetricsRepository | insert_metric(), query_range(), aggregate() | UI 渲染 |
| AlertsRepository | insert_alert(), query_alerts() | 告警检测 |
| SessionsRepository | record_snapshot(), query_sessions() | 采集逻辑 |

---

## 4. 数据模型设计原则

### Runtime vs History 分离

| 类型 | 模型 | 生命周期 | 来源 |
|------|------|----------|------|
| **Runtime** | MonitorFrame, NodeState, AlertState | 秒级，运行时 | Collector → Store |
| **History** | MetricRecord, AlertHistory, SessionRecord | 分钟/月级，持久化 | Storage Writer → SQLite |

**禁止**：

```python
# ❌ 污染 Runtime Model
class MonitorFrame:
    history: list  # 不要给 frame 加历史字段
```

**推荐**：

```python
# ✅ 独立 Record 模型
class MetricRecord:
    node_id: str
    metric: str
    value: float
    timestamp: float
```

---

## 5. Phase 5-1 范围

### 做

| 项 | 说明 |
|----|------|
| host/storage/ | 新建 package |
| database.py | SQLite connection + lifecycle |
| schema.py | Table definition + version |
| repositories/ | MetricsRepository 基础接口 |
| 测试 | test_v52_storage.py |

### 不做

| 项 | 理由 |
|----|------|
| UI / Chart | Phase 5-4 |
| HistoryPage | Phase 5-4 |
| Retention | Phase 5-5 |
| Collector 大改造 | Phase 5-2 |
| Alert 历史迁移 | Phase 5-2 |

---

## 6. 数据写入边界

### 推荐路径

```
Collector (每秒)
    │
    v
Monitor Service / DataController
    │
    ├──→ Runtime State (FrameStore / NodeStore)
    │
    └──→ Storage Writer (Phase 5-2)
              │
              v
         Repository
              │
              v
            SQLite
```

### 禁止

```python
# ❌ Collector 直接写库
class CpuCollector(BaseCollector):
    def collect(self):
        data = ...
        sqlite.insert(data)  # 禁止
```

---

## 7. Facade 规划

延续 Settings 验证过的模式：

```
HistoryPage (Phase 5-4)
    │
HistoryVM
    │
HistoryFacade
    │
Repository
    │
SQLite
```

Phase 5-1 只建立 Storage 基础层，不提前创建 Facade/UI。

---

## 8. 测试策略

### 新增

```
tests/test_v52_storage.py
```

### 覆盖

| 场景 | 验证 |
|------|------|
| Database | create, schema version, migration |
| Repository | insert, query, empty result |
| Isolation | UI 不 import sqlite3, VM 不 import sqlite3 |
| Schema | version check, table existence |

---

## 9. 风险控制

| 风险 | 控制 |
|------|------|
| Storage 污染 runtime | Record 模型与 MonitorFrame 分离 |
| 页面直接查库 | Facade boundary |
| JSON 历史方案 | 禁止，必须 SQLite |
| Schema 频繁变化 | migration version 机制 |
| 写入阻塞 UI | Phase 5-3 引入 async/queue |
| 数据库锁 | WAL mode + 连接池 |

---

## 10. Phase 5 路线

```
Phase 5-1  Storage Foundation      ← 当前
    │
Phase 5-2  Metrics Persistence
    │
Phase 5-3  History Query API
    │
Phase 5-4  History UI
    │
Phase 5-5  Retention / Cleanup
```

### Phase 5-1 验收标准

| 项目 | 目标 |
|------|------|
| host/storage exists | ✅ |
| SQLite schema versioned | ✅ |
| Repository layer exists | ✅ |
| Runtime models unchanged | ✅ |
| UI no storage dependency | ✅ |
| Facade boundary preserved | ✅ |
| storage tests pass | ✅ |
| full regression no regression | ✅ |
