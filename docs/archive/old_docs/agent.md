# Agent 开发说明

> **Version**: v5.0
> **Status**: Current
> **Compatibility**: 副机端（服务端），需配合 Host v5.0

## 1. 定位

Agent 是运行在**每台被监控电脑**上的后台服务：采集本机硬件数据、提供 WebSocket/REST 服务、可选本机仪表盘。后台模式无界面，可用 `pythonw` / 打包 exe 静默运行。

## 2. 模块结构

```
agent/
 ├── __init__.py / __main__.py / main.py   # python -m agent 入口
 ├── config.py            # agent_config.json 读写
 ├── http_server.py       # REST API（/api/health|nodes|scan|config）
 ├── websocket_server.py  # WS 服务端（/ws 多订阅推送 + 鉴权 + PING/loss）
 ├── discovery.py         # UDP/mDNS 广播与注册（agent_heartbeat）
 ├── aggregator.py        # 数据聚合器（最新帧缓存）
 ├── self_monitor.py      # 性能兜底（复用 common.self_monitor）
 └── gui/
     └── main_window.py   # 本机仪表盘（--gui 模式，可选）
```

## 3. 启动方式

```bash
python -m agent             # 默认后台服务（无界面）
python -m agent --tray      # 后台服务 + 系统托盘（可打开仪表盘/退出，v5.1）
python -m agent --gui       # 管理员模式：后台服务 + 本机仪表盘（PyQt5）
python -m agent --install-startup   # 装开机自启（schtasks，需管理员）
python -m agent --remove-startup    # 卸开机自启
```

## 4. 启动流程

1. 解析命令行参数
2. 单实例检测（`Global\PC_Monitor_Agent`）
3. 初始化日志 → `logs/agent.log`
4. 加载配置 `agent_config.json`
5. 端口占用检测（12345 / 12346）
6. 启动采集器线程池（`common/collectors`）
7. 启动聚合器（每秒 → 最新帧缓存）
8. 启动 aiohttp 应用：REST `/api/*` + WS `/ws`（同端口）
9. 启动 WS 推送协程 + UDP/mDNS 广播
10. 进入 asyncio 事件循环

## 5. 核心模块

### 采集器

复用 `common/collectors/`（CPU/GPU/内存/磁盘/网络/FPS/进程/系统/网络质量）。每个采集器独立线程、异常隔离、线程安全读取。配置中可开关（`collectors.gpu` / `collectors.fps`）。

### 聚合器（aggregator.py）

每秒从各采集器 `get()` 组装 `monitor_data` 帧，写入**线程安全最新帧缓存**。WS 推送协程从缓存读取广播。

### WebSocket 服务端

- 路由 `/ws`，查询参数 `?token=` 鉴权（推荐）
- 每秒向所有订阅者广播 `monitor_data`
- 30s 心跳保活；响应 `loss_ping`/`loss_pong`

### REST 服务端

`GET /api/health`、`GET /api/nodes`、`POST /api/scan`、`GET/POST /api/config`。详见 [api.md](api.md)。

## 6. 配置

`agent_config.json` 字段：

| 字段 | 说明 |
|------|------|
| `http_port` | HTTP/WS 共用端口（默认 12345） |
| `udp_port` | UDP 自动发现端口（默认 12346） |
| `token` | 鉴权 token（首次启动自动生成） |
| `use_multicast` | 是否用组播替代广播 |
| `preferred_iface` | 指定网卡名 |
| `gpu_index` | 多 GPU 时主卡 index |
| `collectors` | 采集开关（fps/gpu/temperature） |
| `log_level` | 日志级别 |

## 7. 运维

- **单实例**：命名互斥体 `Global\PC_Monitor_Agent`
- **自启**：`--install-startup`（schtasks `/RL HIGHEST`，需管理员）
- **性能兜底**：CPU > 5% 连续 2 次 → 采集频率降为 2s + 关帧率；< 3% 恢复
- **日志**：`logs/agent.log`，10MB/5 份轮转
