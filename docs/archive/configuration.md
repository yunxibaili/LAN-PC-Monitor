# 配置说明

> **Version**: v5.0
> **Status**: Current
> **Compatibility**: Agent/Host 配置文件（首次启动自动生成）

配置文件在首次启动时自动生成（含随机 token）。

## 1. Agent 配置（agent_config.json）

```json
{
  "http_port": 12345,
  "udp_port": 12346,
  "token": "auto_generated",
  "use_multicast": false,
  "preferred_iface": "",
  "gpu_index": 0,
  "collectors": {"fps": "presentmon", "gpu": true, "temperature": true},
  "log_level": "INFO"
}
```

| 字段 | 默认 | 说明 |
|------|------|------|
| `http_port` | 12345 | HTTP/WS 共用端口 |
| `udp_port` | 12346 | UDP 自动发现端口 |
| `token` | 自动 | 鉴权 token（仅配置文件可改） |
| `use_multicast` | false | true 用组播 239.0.0.1 |
| `preferred_iface` | "" | 指定网卡名 |
| `gpu_index` | 0 | 多 GPU 主卡 index |
| `collectors.fps` | "presentmon" | "presentmon"/"dxgi"/false |
| `collectors.gpu` | true | GPU 采集开关 |
| `collectors.temperature` | true | 温度采集开关 |
| `log_level` | INFO | DEBUG/INFO/WARNING/ERROR |

## 2. Host 配置（host_config.json）

```json
{
  "hosts": [],
  "window_geometry": {"x":100,"y":100,"w":1400,"h":900},
  "view_mode": "auto",
  "max_overview_cards": 16,
  "udp_port": 12346,
  "log_level": "INFO",
  "alert_popup": true,
  "language": "zh_CN"
}
```

| 字段 | 说明 |
|------|------|
| `hosts` | Agent 列表（node_id/ip/port/token/alias） |
| `view_mode` | auto/single/multi/overview |
| `alerts` | 红线告警规则（数组） |
| `language` | 界面语言（zh_CN/en） |

## 3. v6.0 规划

- 配置热更新：`POST /api/config/reload`（无需重启）
- token 过期：`token_expire_days` 字段
