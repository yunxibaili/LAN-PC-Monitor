# Agent/Host 通信协议

> **Version**: v5.0
> **Status**: CURRENT

## 1. 通道总览

| 通道 | 用途 | 端口 |
|------|------|------|
| WebSocket `/ws` | 实时推送监控数据 | 12345 |
| REST `/api/*` | 辅助功能 | 12345 |
| UDP | 自动发现心跳 | 12346 |

## 2. WebSocket 推送

### 连接

```
ws://<agent_ip>:12345/ws?token=xxx
```

### 流程

```
Host                              Agent
 │  连接 ws://ip:12345/ws?token   │
 │──────────────────────────────→│
 │       auth_result{ok:true}     │
 │←──────────────────────────────│
 │       monitor_data (每秒)      │
 │←──────────────────────────────│
 │   loss_ping (每10s ×3)         │
 │──────────────────────────────→│
 │   loss_pong                    │
 │←──────────────────────────────│
```

### 消息类型

| type | 方向 | 用途 |
|------|------|------|
| `monitor_data` | Agent→Host | 1秒监控数据帧 |
| `auth_result` | Agent→Host | 鉴权结果 |
| `loss_ping` / `loss_pong` | 双向 | 丢包测量 |

## 3. monitor_data 帧结构

```json
{
  "type": "monitor_data",
  "ts": 1722892800.123,
  "hostname": "GAME-PC",
  "cpu": {
    "name": "Intel Core i7-7700K",
    "total_usage": 45.2,
    "package_temp_c": 65.0,
    "physical_cores": 4,
    "power_w": 85.0
  },
  "gpu": {
    "name": "RTX 3070",
    "usage_percent": 62.0,
    "core_temp_c": 68.0,
    "vram_used_mb": 4096,
    "power_w": 120.0
  },
  "ram": {
    "total_gb": 32.0,
    "used_gb": 16.0,
    "usage_percent": 50.0
  },
  "disk": [{"drive":"C:","read_mb_s":120,"write_mb_s":45,"usage_percent":60}],
  "net": {"upload_mb_s":1.2,"download_mb_s":5.6,"link_speed_mbps":1000},
  "net_quality": {"quality_score":98,"latency_to_gateway_ms":2.1,"packet_loss_percent":0},
  "fps": {"fps":142,"frame_time_ms":7.0,"window_title":"Game"},
  "processes": {"top_cpu":[{"name":"chrome","usage_percent":12}]}
}
```

## 4. REST API

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/nodes` | GET | 节点列表 |
| `/api/scan` | POST | 触发发现 |
| `/api/config` | GET/POST | 读写配置 |

鉴权：`Authorization: Bearer <token>` 或 `?token=<token>`

## 5. 超时与重连

- WS 超时：30 秒无消息视为断开
- 重连：指数退避 1s→2s→4s→...→60s 封顶
- 已配置 Agent 即使离线也保留，持续重连

## 6. 丢包测量

- **到网关丢包**：`net_quality.packet_loss_percent` (系统 ping)
- **WS 链路丢包**：每 10s 3 个 `loss_ping`，统计回复率
