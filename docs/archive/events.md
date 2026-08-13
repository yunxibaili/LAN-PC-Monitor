# 事件系统

> **Version**: v6.0（规划）
> **Status**: **Design Draft** —— 仅设计稿，**未实现**，请勿误以为当前可用
> **Compatibility**: 计划新增模块，参考 Zabbix Trigger；不影响现有告警（红线告警为 Host 侧已实现）

---

## 0. Implementation Plan

| 步骤 | 内容 | 产出 |
|------|------|------|
| 1 | `event/event_manager.py`：事件记录/去重/恢复状态机 | 事件生命周期 |
| 2 | 事件持久化（写入存储事件表） | 历史事件可查 |
| 3 | 阈值判定接入（温度/磁盘/评分/FPS） | 自动触发事件 |
| 4 | `GET /api/events` + Host 事件查看 | 事件查询 API |
| 5 | 与 collector watchdog / node_manager 联动 | 采集器/节点事件 |

> 尚未开始实施。状态更新见 [changelog.md](changelog.md)。

---

## 1. 目标

统一管理告警事件（而非分散在各采集器/告警逻辑），支持规则判断、告警生命周期（触发/恢复）。

## 2. 事件结构

```json
{
  "id": "evt_169",
  "type": "CPU_TEMP_HIGH",
  "level": "WARNING",
  "message": "CPU 温度 88°C 超过阈值 85°C",
  "timestamp": 1722892801.0,
  "recovered": false
}
```

| 等级 | 说明 |
|------|------|
| `INFO` | 常规状态变化 |
| `WARNING` | 需关注 |
| `CRITICAL` | 严重 |

## 3. 内置事件类型

| type | 触发条件 | 等级 |
|------|----------|------|
| `CPU_TEMP_HIGH` | CPU 温度超阈值 | WARNING |
| `GPU_TEMP_HIGH` | GPU 温度超阈值 | WARNING |
| `DISK_LOW` | 磁盘使用率超阈值 | WARNING |
| `NET_ANOMALY` | 网络评分低 / 丢包高 | WARNING |
| `FPS_DROP` | FPS 低于阈值 | WARNING |
| `AGENT_ERROR` | 自监控异常 | CRITICAL |
| `COLLECTOR_DEGRADED` | 采集器 watchdog 触发 | WARNING |
| `NODE_OFFLINE` | 节点离线 | WARNING |

## 4. 模块

```
event/
 └── event_manager.py    # 记录 / 去重 / 恢复 / 查询
```

- **去重**：同类型未恢复事件不重复记录（状态机 `active → recovered`）。
- **持久化**：写入存储的事件表（可查历史）。
- **对外**：`GET /api/events?level=WARNING&recovered=false`。

## 5. 触发源

事件由以下模块产生：

- 采集数据阈值判定（温度/磁盘/评分/FPS）
- Agent 自监控（agent_metrics）
- 采集器 watchdog（collector_degraded）
- 节点状态机（node_offline）
