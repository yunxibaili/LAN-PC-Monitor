# 架构设计

> **Version**: v5.0
> **Status**: Current
> **Compatibility**: v4.0 之前的 TCP 协议已不兼容；`monitor_data` JSON Schema 自 v4.0 起保持稳定

---

## 1. 总体架构

```
        Host（监控大屏 · PyQt5）
            │
      WebSocket / REST（多连接）
            │
     ┌──────┴──────┐
     │ Agent Nodes  │  每台被监控电脑
     └──┬───┬───┬──┘
        │   │   │
   Collector Storage Event
    (采集)  (存储) (事件)
```

**双角色前后端分离**：

| 角色 | 程序 | 网络角色 | GUI | 职责 |
|------|------|----------|-----|------|
| **Agent（副机端）** | `python -m agent` | HTTP/WS **Server** (12345) | 可选本机仪表盘（PyQt5） | 采集 + 推送 + REST API |
| **Host（主机端）** | `python -m host` | HTTP/WS **Client**（多连接） | 集中监控大屏 | 订阅 + 展示 + 节点管理 |

## 2. 拓扑约束

- 同一 Agent 可被**多台 Host 同时连接订阅**（WebSocket 多客户端广播）。
- **Agent 之间不直接通信**；每台 Agent 只提供本机数据。
- Host 通过配置的 Agent 地址列表（IP + 端口）分别连接。
- 支持多 Host 同时连接同一 Agent（副机端 + 监控端并存）。

## 3. 数据流

### 3.1 实时数据流（Agent → Host）

```
采集器(每秒) → 聚合器(组装 monitor_data) → 最新帧缓存
                                        ↓
                              WebSocket 广播(每秒)
                                        ↓
                                   Host 各节点连接
                                        ↓
                                   GUI 信号槽渲染
```

### 3.2 控制流（Host → Agent）

```
Host 发送 → auth/loss_ping → Agent 校验/回显 → Host 计算 RTT/丢包
```

## 4. WebSocket 流程

```
Host                              Agent
 │  连接 ws://ip:12345/ws?token=xxx  │
 │──────────────────────────────────→│
 │          auth_result{ok:true}     │
 │←──────────────────────────────────│
 │          monitor_data (每秒)      │
 │←──────────────────────────────────│
 │   loss_ping (每10s ×3)            │
 │──────────────────────────────────→│
 │   loss_pong                      │
 │←──────────────────────────────────│
```

- **鉴权**：URL 查询参数 token（推荐），握手阶段校验；失败 close 1008 / HTTP 403。
- **推送**：每秒广播 `monitor_data`（多客户端）。
- **RTT**：WS PING 控制帧 + `loss_pong` 回显 `perf_counter` 时间戳精确测量。
- **重连**：断线独立指数退避 1s→60s 封顶。

## 5. REST 流程

```
Host                                  Agent
 │  GET /api/health?token=xxx          │
 │────────────────────────────────────→│
 │  {status,version,uptime,subscribers}│
 │←────────────────────────────────────│
 │  GET /api/nodes                     │
 │  POST /api/scan                     │
 │  GET/POST /api/config               │
```

- 鉴权：`Authorization: Bearer <token>` 或 `?token=`。
- token 不可经 API 修改（仅配置文件）。

## 6. Agent 内部架构

```
┌────────────────────────────────────────────┐
│               Agent（异步服务）              │
│  ┌──────────────────────────────────────┐  │
│  │          采集层（线程池）               │  │
│  │  CPU/GPU/内存/磁盘/网络/FPS/进程/系统  │  │
│  └───────────────────┬──────────────────┘  │
│                      │ get() 1s 节拍       │
│  ┌───────────────────▼──────────────────┐  │
│  │      数据聚合器（最新帧缓存）            │  │
│  └───────┬───────────────┬──────────────┘  │
│  ┌───────▼────────┐  ┌────▼─────────────┐  │
│  │ WebSocket Server│  │ REST Server      │  │
│  │ /ws 多订阅推送   │  │ /api/health|nodes│  │
│  │ 鉴权+PING/loss  │  │ /scan|/config    │  │
│  └─────────────────┘  └─────────────────┘  │
│  单实例 · 日志轮转 · 性能兜底 · 自启         │
└────────────────────────────────────────────┘
```

## 7. Host 内部架构

```
┌────────────────────────────────────────────┐
│        Host（PyQt5 集中大屏）                │
│  ┌──────────────────┐  ┌────────────────┐  │
│  │ 远程连接管理器     │  │ 本机节点(可选)  │  │
│  │ dict→NodeConnection│  │ 本地采集器      │  │
│  └────────┬─────────┘  └───────┬────────┘  │
│           │ data_received      │ local_data │
│  ┌────────▼────────────────────▼────────┐  │
│  │  GUI 主线程（信号槽汇聚）               │  │
│  │  节点列表 / 详情面板 / 概览 / 告警     │  │
│  └───────────────────────────────────────┘  │
│  mDNS/UDP 监听 → 自动发现                   │
└────────────────────────────────────────────┘
```

## 8. common 模块关系

`common/` 为 Agent 与 Host 共用代码，是两端依赖的基石：

```
common/
 ├── collectors/      采集器（Agent 服务 + Host 本机节点共用）
 ├── protocol.py      （v4.0 TCP 遗留，v5.0 已弃用，保留参考）
 ├── utils.py         工具（IP/端口/网关/连接码）
 ├── logger.py        日志（RotatingFileHandler）
 ├── single_instance.py 单实例互斥
 ├── startup.py       开机自启
 ├── quality.py       网络质量评分（滑动平均）
 ├── lhm.py           LibreHardwareMonitor 温度读取
 ├── theme.py         深色主题/变色规则
 ├── i18n.py          国际化
 ├── connect_code.py  连接码/.pcm/剪贴板
 └── self_monitor.py  性能兜底

依赖方向：agent/ → common/，host/ → common/（agent 不依赖 host，host 可依赖 agent 的公共部分）
```

## 9. 线程/协程模型

| 单元 | 归属 | 职责 |
|------|------|------|
| 采集线程 ×N | Agent / Host 本机 | 各采集器独立线程 |
| 聚合线程 | Agent | 1 秒组装帧 → 最新帧缓存 |
| asyncio 事件循环 | Agent | WS 服务 + REST 服务 |
| WS 广播协程 | Agent | 每秒向订阅者广播 |
| 连接线程 ×N | Host | 每 Agent 一个 WS 连接 + 重连 |
| GUI 主线程 | Host | Qt 事件循环 |

## 10. v6.0 扩展位置（Planned）

平台化能力以**独立包**形式接入，不侵入核心：

```
storage/      历史存储（SQLite + 保留策略）
event/        事件系统（规则 + 告警生命周期）
history/      历史查询 API
manager/      节点状态 / 采集器 watchdog / 自监控
```

> **Status**: Planned（v6.0 设计稿，未实现）。详见 [database.md](database.md)、[events.md](events.md)。
