# 通信协议

> **Version**: v5.0
> **Status**: Current（v6.0 订阅模式已标注 Planned）
> **Compatibility**: Agent ↔ Host；`monitor_data` Schema 自 v4.0 稳定

## 1. 总览

| 通道 | 用途 | 说明 |
|------|------|------|
| **WebSocket** `/ws` | 实时推送监控数据 | Agent 每秒推送 `monitor_data` 帧；支持多客户端订阅 |
| **REST** `/api/*` | 辅助功能 | 健康/节点/配置/扫描 |
| **RTT 测量** | WebSocket PING/PONG 帧 | 标准 WS 控制帧，客户端本地时间戳计算 |

默认端口：HTTP/WS **12345**，UDP 自动发现 **12346**。

## 2. WebSocket 数据推送

- **连接**：`ws://<agent_ip>:12345/ws?token=xxx`
- **鉴权**：查询参数 token（推荐），失败关闭（HTTP 403 / WS close 1008）
- **推送**：鉴权通过后每秒广播一条 `monitor_data` 文本帧
- **多客户端**：Agent 维护订阅者集合，广播给所有订阅者
- **RTT**：Host 发 WS PING 帧，Agent 底层自动回 PONG，Host 本地 `perf_counter` 计算

```python
# Agent 端：aiohttp 示意
async def push_loop():
    while True:
        frame = aggregator.latest_frame()
        for ws in list(subscribers):
            try:
                await ws.send_str(json.dumps(frame, ensure_ascii=False))
            except Exception:
                subscribers.discard(ws)
        await asyncio.sleep(1.0)
```

## 3. 消息类型

| type | 方向 | 用途 | 说明 |
|------|------|------|------|
| `monitor_data` | Agent→Host | 1 秒监控数据帧 | Schema 见 §5 |
| `auth` | Host→Agent | 鉴权（首帧备选） | `{"type":"auth","token":"xxx"}` |
| `auth_result` | Agent→Host | 鉴权结果 | `{"ok":true}` / `{"ok":false,"reason":...}` |
| `agent_heartbeat` | Agent→局域网(UDP) | 自动发现心跳 | `hostname/ip/http_port/token/ts` |
| `loss_ping` / `loss_pong` | 双向 | WS 链路丢包测量（低频） | `{"seq":N,"ts":...}` |
| `error` | Agent→Host | 错误通知 | `{"code":..., "message":...}` |

## 4. 鉴权流程

1. Agent 配置 `token`（默认随机生成）。
2. Host 连接 `ws://ip:12345/ws?token=xxx`（推荐）；或首帧 `{"type":"auth","token":"xxx"}`。
3. Agent 校验：匹配 → 加入订阅者推送；不匹配 → 关闭（close 1008 / 403）。
4. REST 请求在 `Authorization: Bearer <token>` 头或 `?token=` 参数携带 token。

> token 明文传输，仅防误连（LAN 可信环境）。v6.0 规划 token 过期/权限分级。

## 5. monitor_data JSON Schema

每秒推送的完整数据帧：

```json
{
  "type": "monitor_data",
  "ts": 1722892800.123,
  "hostname": "GAME-PC",
  "connected_clients": 2,
  "system": {"uptime_seconds": 86400, "local_ip": "192.168.1.100"},
  "cpu": {
    "name": "Intel Core i7-7700K",
    "total_usage": 45.2,
    "per_core_usage": [30.1, 52.3, 40.0, 58.5],
    "physical_cores": 4, "logical_cores": 8,
    "core_freq_mhz": 4200, "package_temp_c": 65.0, "power_w": 85.0
  },
  "ram": {
    "total_gb": 32.0, "used_gb": 16.0, "available_gb": 16.0,
    "usage_percent": 50.0, "swap_used_mb": 512.0
  },
  "gpu": {
    "name": "NVIDIA GeForce RTX 3070",
    "usage_percent": 62.0, "vram_used_mb": 4096, "vram_total_mb": 8192,
    "vram_usage_percent": 50.0, "core_temp_c": 68.0, "mem_temp_c": "N/A",
    "hotspot_temp_c": 75.0, "core_freq_mhz": 1800, "mem_freq_mhz": 7000,
    "power_w": 120.0, "power_limit_w": 250.0,
    "engine_usage": {"graphics":62.0,"compute":5.0,"encode":0.0,"decode":0.0},
    "top_vram_processes": [{"name":"game.exe","vram_mb":2048}]
  },
  "disk": [
    {"drive":"C:","read_mb_s":120.5,"write_mb_s":45.2,
     "read_iops":1500,"write_iops":800,"queue_depth":1.2,
     "temp_c":"N/A","free_gb":200.0,"total_gb":500.0,"usage_percent":60.0}
  ],
  "net": {
    "interface":"以太网", "upload_mb_s":1.2, "download_mb_s":5.6,
    "link_speed_mbps":1000, "errors_sent":0,"errors_recv":0,
    "drops_sent":0,"drops_recv":0
  },
  "net_quality": {
    "latency_to_client_ms": null, "latency_to_gateway_ms": 2.1,
    "packet_loss_percent": 0.0, "quality_score": 98, "quality_grade": "优秀"
  },
  "fps": {
    "window_title":"Cyberpunk 2077", "fps":142,
    "frame_time_ms":7.0, "low_1_percent":98, "source":"presentmon"
  },
  "processes": {
    "top_cpu": [{"name":"chrome.exe","usage_percent":12.0}],
    "top_gpu": [{"name":"game.exe","usage_percent":65.0}]
  }
}
```

**约定**：

- 无法获取的字段统一 `"N/A"` 或 `null`，GUI 识别后显示 N/A 并跳过变色。
- `net_quality.latency_to_client_ms`：Agent 端填 `null`，RTT 由各 Host 本地测量。

## 6. 超时与重连

- 每 Agent 连接 WS 超时 30 秒（无消息视为断开）。
- 断线独立指数退避：1s→2s→4s→8s→16s→32s→60s 封顶，连上后重置。
- 已配置 Agent 即使离线也保留，持续重连。

## 7. 丢包测量

- **到网关丢包（主）**：`net_quality.packet_loss_percent` 由系统 `ping` 解析。
- **WS 链路丢包（补充）**：Host 每 10 秒发 3 个 `loss_ping`，Agent 回 `loss_pong`，统计回复率。

## 8. v6.0 扩展（规划）

- **订阅模式**：客户端发送 `{"type":"subscribe","metrics":["cpu","gpu","fps"]}`，Agent 按订阅推送（full / lite）。
- 不发送订阅消息的客户端保持默认 full 模式（向后兼容）。
