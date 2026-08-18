# 数据存储设计

> **Version**: v6.0（规划）
> **Status**: **Design Draft** —— 仅设计稿，**未实现**，请勿误以为当前可用
> **Compatibility**: 计划新增模块，不影响现有 `monitor_data` Schema 与实时功能

---

## 0. Implementation Plan

| 步骤 | 内容 | 产出 |
|------|------|------|
| 1 | `storage/database.py`：SQLite 建表 + 写入 | 实时指标落库 |
| 2 | `storage/retention.py`：保留策略 + retention worker | 24h/30d/1y 自动清理与聚合 |
| 3 | `history/` 查询模块 + `GET /api/history` | 历史趋势 API |
| 4 | 与聚合器集成（每秒抽样写入，批量落库） | 不阻塞采集线程 |
| 5 | 回归验证（test_api + Schema 不变） | 全量自检通过 |

> 尚未开始实施。状态更新见 [changelog.md](changelog.md)。

---

## 1. 目标

当前系统仅有实时帧缓存。新增**时间序列数据存储**，支撑历史趋势查询与长期分析。

## 2. 技术选型

| 方案 | 说明 | 适用 |
|------|------|------|
| **SQLite（默认）** | Python 内置 `sqlite3`，单文件 `data/agent_history.db` | 单 Agent 本地，轻量首选 |
| **InfluxDB（可选）** | 时间序列数据库，HTTP 写入 | 集中存储 / 大数据量 |

## 3. 模块结构

```
storage/
 ├── database.py      # SQLite 连接管理 / 建表 / 读写
 ├── models.py        # 指标点数据结构 / 聚合模型
 └── retention.py     # 保留策略 + 自动清理
```

## 4. 保存指标

| 指标名 | 来源 | 说明 |
|--------|------|------|
| `cpu_usage` | `cpu.total_usage` | CPU 使用率 |
| `gpu_usage` | `gpu.usage_percent` | GPU 使用率 |
| `gpu_temp` | `gpu.core_temp_c` | GPU 温度 |
| `ram_usage` | `ram.usage_percent` | 内存占用 |
| `disk_io` | `disk[].read_mb_s/write_mb_s` | 磁盘 IO |
| `net_traffic` | `net.upload/download_mb_s` | 网络流量 |
| `fps` | `fps.fps` | 帧率 |
| `quality_score` | `net_quality.quality_score` | 网络质量评分 |

## 5. 保留策略

| 粒度 | 聚合 | 保留 |
|------|------|------|
| 实时（原始点） | 每秒原始值 | 24 小时 |
| 分钟级 | AVG/MAX/MIN | 30 天 |
| 小时级 | AVG/MAX/MIN | 1 年 |

**retention worker**：每天执行一次，删除过期数据；定期将原始数据聚合成分钟/小时级。

## 6. 表设计（SQLite）

```sql
CREATE TABLE IF NOT EXISTS metric_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric TEXT NOT NULL,
    timestamp REAL NOT NULL,
    value REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_raw_metric_ts ON metric_raw(metric, timestamp);

CREATE TABLE IF NOT EXISTS metric_min (
    metric TEXT NOT NULL, bucket INTEGER NOT NULL,
    avg REAL, max REAL, min REAL
);
CREATE TABLE IF NOT EXISTS metric_hour (
    metric TEXT NOT NULL, bucket INTEGER NOT NULL,
    avg REAL, max REAL, min REAL
);
```

## 7. 查询 API

`GET /api/history?metric=<metric>&start=<ts>&end=<ts>&interval=<raw|min|hour>`

详见 [api.md](api.md)。
