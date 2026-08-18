# API 文档

> **Version**: v5.0
> **Status**: Current（v6.0 规划接口已标注 Planned）
> **Compatibility**: Agent REST API，需 token 鉴权

所有 REST 请求需携带 token：`Authorization: Bearer <token>` 或 `?token=<token>`。

## 1. 现有接口

### `GET /api/health` — 健康检查

```json
{
  "status": "ok",
  "version": "5.0.0",
  "hostname": "GAME-PC",
  "ip": "192.168.1.100",
  "uptime": 86400,
  "subscribers": 2
}
```

### `GET /api/nodes` — 本机信息与节点列表

```json
{
  "self": {
    "hostname": "GAME-PC",
    "ip": "192.168.1.100",
    "port": 12345,
    "alias": "游戏主机"
  },
  "nodes": [
    {"node_id":"a1b2c3","ip":"192.168.1.124","port":12345,
     "alias":"副机B","status":"online"}
  ]
}
```

### `POST /api/scan` — 触发自动发现扫描

请求体（可选）：`{"timeout": 3}`

```json
{
  "found": [
    {"hostname":"GAME-PC-2","ip":"192.168.1.124","port":12345,
     "token_hash":"a1b2c3d4"}
  ]
}
```

> `token_hash` 为 token 的 SHA-256 前 8 位，不泄露完整 token。

### `GET /api/config` — 读取配置

```json
{
  "http_port": 12345,
  "udp_port": 12346,
  "collectors": {"fps": "presentmon", "gpu": true, "temperature": true},
  "log_level": "INFO",
  "gpu_index": 0
}
```

> **不返回 token**（敏感字段排除）。token 仅通过配置文件修改，不提供 API。

### `POST /api/config` — 更新配置

请求体：`{"alias": "新别名", "log_level": "DEBUG"}` → `{"ok": true}`

支持更新别名、日志级别、采集开关等；**token 不可经此接口修改**。

## 2. v6.0 规划接口（Planned）

> ⚠️ 以下接口为 v6.0 **设计稿，尚未实现**。请勿在当前 v5.0 中调用。

### `GET /api/history` — 历史趋势查询

参数：`metric`、`start`、`end`、`interval`（raw/min/hour）

```json
{
  "metric": "gpu_usage",
  "start": 1722892800,
  "end": 1722896400,
  "interval": "raw",
  "points": [
    {"timestamp": 1722892801, "value": 75.0}
  ]
}
```

### `POST /api/config/reload` — 配置热更新

请求体：`{"collectors": {"fps": "dxgi"}, "gpu_index": 1, "log_level": "DEBUG"}` → `{"ok": true}`

无需重启 Agent。

### `GET /api/version` — 版本信息

```json
{
  "agent_version": "5.1.0",
  "protocol_version": "1.0",
  "schema_version": "monitor_data_v5",
  "update_time": "2026-08-10T20:00:00+08:00"
}
```

### `GET /api/summary` — 批量聚合视图

```json
{
  "total_nodes": 20,
  "online": 18,
  "offline": 2,
  "avg_quality": 95
}
```

### `GET /api/events` — 事件查询

参数：`level`（INFO/WARNING/CRITICAL）、`recovered`（true/false）

### `GET /api/logs` — 日志查询

参数：`category`（agent/collector/network/event）、`level`、`limit`（默认 100）

### `POST /api/token/refresh` — token 刷新

请求体：`{"old_token": "...", "role": "admin"}`

完整设计见 [events.md](events.md) 与 README 第五篇（v6.0 规划）。
