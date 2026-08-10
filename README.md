# 局域网硬件监控系统（LAN PC Monitor）v5.0 · 前后端分离版

基于 **HTTP/REST + WebSocket** 的局域网硬件实时监控系统，Windows 10/11，Python 3.10+。

**v5.0 双角色架构**：副机端 **Agent（服务端）** ＋ 主机端 **Host（纯前端）**。取消独立的采集节点（Node），采集能力与 API 服务整合到 Agent；Host 通过标准 WebSocket/REST 拉取或订阅数据，形成经典"前后端分离"模式。

> **文档状态**：本文件为 v5.0 重构版**唯一技术文档**（设计基线），整合系统技术规格、前后端交互协议（WebSocket/REST API）、采集方案、多语言（i18n）、自定义红线告警五部分。
>
> **迁移说明**：当前代码库基线为 v4.0（采集节点/副机端/主机端三角色，TCP+UDP/mDNS）。本文件描述 v5.0 目标架构；重构按 §25 实施步骤逐模块迁移，迁移期间保持 `monitor_data` 数据帧格式不变。

## 架构

| 角色 | 启动方式 | 网络角色 | GUI | 说明 |
|------|----------|----------|-----|------|
| **副机端 Agent** | `python -m agent` | HTTP/WebSocket **Server** (12345) | 可选：原生本机仪表盘（PyQt5） | 每台被监控电脑运行的后台服务：采集 + API + 推送 |
| **主机端 Host** | `python -m host` | HTTP/WebSocket **Client**（多连接） | 集中监控大屏 | 连接所有 Agent，集中展示所有节点完整数据 |

- 同一 Agent 可被多台 Host（及多台浏览器）同时连接订阅（WebSocket 多客户端广播）。
- Agent 之间**不直接通信**；每台 Agent 只提供本机数据。
- Host 通过配置的 Agent 地址列表（IP + 端口）分别连接，实时拉取/订阅。

## 功能特性

- **实时采集**：CPU / 内存 / 磁盘（含队列深度）/ 网络速率 / 进程 TOP / 系统信息 / GPU（NVML 全指标，AMD pyadl 可选）/ 温度（LibreHardwareMonitor）
- **网络质量**：RTT 实测 + 丢包测量 + 滑动平均评分（阈值变色）
- **帧率采集**：PresentMon CLI 主方案（前台窗口动态绑定 + 1% Low），无工具时自动降级 DXGI 截帧
- **前后端分离**：WebSocket 每秒推送 `monitor_data` 帧（格式与 v4.0 完全一致，§8）；REST API 提供节点/配置/健康/扫描等辅助能力（§4.5）
- **自动发现（可选）**：mDNS（`_pcmonitor._tcp.local.`）＋ UDP 广播互为备份，发现后经 HTTP API 补全详情；`pcmonitor://` 剪贴板连接串；`.pcm` 配置一键导入导出；首屏引导一键接入
- **运维能力**：鉴权（token）、自动重连（指数退避）、单实例互斥、端口占用检测、日志轮转、开机自启（Agent 服务化 / Host 注册表）、性能兜底（CPU 超限自动降级频率）
- **深色主题**：集中大屏自适应三模式（概览/详情/自动），阈值三级变色
- **双端独立打包（强制）**：Agent 与 Host 独立构建、独立安装包、独立安装目录与配置，互不混装（§16.5）
- **可扩展**：Host 保留 PyQt5 原生桌面 GUI，打包为独立 exe；Agent 为后台服务，可选原生本机仪表盘

## 快速开始

```bash
# 开发/调试：一键安装全部依赖
pip install -r requirements-agent.txt -r requirements-host.txt
# 或按角色安装（见 §16.1）：
#   仅 Agent 端:  pip install -r requirements-agent.txt
#   仅 Host 端:   pip install -r requirements-host.txt

python -m agent            # 1) 副机端 Agent（被监控端，建议管理员运行；后台服务，无界面）
python -m agent --gui      #    可选：后台服务 + 本机仪表盘 GUI（PyQt5）
python -m host             # 2) 主机端 Host（集中监控大屏，无需提权）
```

首次启动自动生成 `agent_config.json`（含随机 token）；Host 首屏引导自动发现 Agent，一键接入。

防火墙需放行 TCP 12345（HTTP/WebSocket）与 UDP 12346（自动发现，可选）。见 §16.2。

## 测试

```bash
python tests/test_p0.py        # 协议/鉴权/链路/发现/评分器/采集器冒烟
python tests/test_connect.py   # 双端连接端到端（鉴权/数据帧/RTT/丢包/断线清理）
python tests/test_p4.py        # 真实进程双端集成（重连/多客户端/mDNS/降级链路）
python tests/test_api.py       # （新增）REST API 与 WebSocket 订阅端到端
```

## 目录结构（v5.0）

```
├── common/                     # 协议/工具/日志/主题/评分/LHM/单实例/自启/连接码/连接对话框
│   └── collectors/             # 采集器（v5.0 已从 node/collectors 迁移至此，Agent 与 Host 本机节点共用）
│   └── self_monitor.py         # 性能兜底（v5.0 已从 host/ 提升至此，Agent 与 Host 共用）
├── agent/                      # 副机端（config/aggregator/http_server/websocket_server/discovery/self_monitor/gui/main）
│   └── gui/                    # 本机仪表盘（PyQt5，--gui 模式）
├── host/                       # 主机端（connection/discovery/local_node/self_monitor/alerts/gui*）
├── tests/                      # test_p0 / test_connect / test_p4 / test_api
├── tools/PresentMon.exe        # 帧率工具（需手动下载）
└── logs/                       # 运行日志（自动创建）
```

## 实施进度

v4.0（三角色）P0-P5 全部完成，自检基线：`test_p0` **63/63**、`test_connect` **17/17**、`test_p4` **44/44**（当前环境缺 PyQt5，实际运行 test_p0 53 通过/3 跳过）。

v5.0（前后端分离）迁移阶段详见 §25：
- **M1 ✅ 完成**：采集器从 `node/collectors/` 迁至 `common/collectors/`；`SelfMonitor` 从 `host/` 提升至 `common/self_monitor.py`；旧 `node/`、`client/` 目录删除。
- **M2 ✅ 完成**：`agent/` 服务实现——`config`/`aggregator`（最新帧缓存）/`websocket_server`（/ws 鉴权+推送+loss_ping/pong）/`http_server`（/api/health|nodes|scan|config）/`discovery`/`main`（aiohttp 单应用）。新增 `tests/test_api.py` **14/14 通过**。
- **M2b ✅ 完成**：Agent 本机仪表盘 `agent/gui/`（PyQt5，`--gui` 模式，Qt 主循环 + 后台服务 QThread）。
- **M3 ✅ 完成**：Host 网络层 TCP→WebSocket——`host/connection.py` 重写为 `NodeConnection`（websocket-client，`ws://ip:port/ws?token=`），信号接口与 v4.0 完全兼容，GUI 零改动；RTT 经 loss_pong 精确测量；沙箱端到端 8/8 通过。
- **M4 待办**：便捷连接/鉴权迁移。
- **M5 待办**：打包与验收（**强制双端分离打包**，§16.5）。

---

# 技术规格与设计文档

# 第一篇 · 系统技术规格（v5.0）

> 版本：v5.0（前后端分离）　日期：2026-08-10　适用平台：Windows 10 / 11
>
> **v5.0 重大变更**：相对 v4.0 三角色架构，取消独立采集节点（Node），将采集能力与 API 服务整合到**副机端 Agent**，主机端 Host 改为**纯前端应用**，通信从 TCP 自定义协议 + UDP 广播升级为 **HTTP/REST + WebSocket**。
> - **副机端 Agent（服务端）**：每台被监控电脑运行一个后台服务，① 1 秒采集本机硬件数据 ② 提供 WebSocket（实时推送）与 REST API（辅助功能）③ 可选原生本机仪表盘（PyQt5）④ 节点管理 API。
> - **主机端 Host（纯前端）**：可部署于任意电脑，通过网络请求连接所有 Agent，集中展示数据；负责节点配置持久化、阈值变色、自定义红线告警。
>
> **数据帧格式完全保留**：`monitor_data` JSON Schema 与 v4.0 §8 一致，便于逐步迁移、兼容既有解析端。

---

## 目录

1. [项目概述](#1-项目概述)
2. [角色与通信拓扑](#2-角色与通信拓扑)
3. [系统架构设计](#3-系统架构设计)
4. [通信协议设计（WebSocket + REST）](#4-通信协议设计websocket--rest)
5. [副机端设计（Agent · 服务端）](#5-副机端设计agent--服务端)
6. [主机端设计（Host · 纯前端）](#6-主机端设计host--纯前端)
7. [数据格式规范（JSON Schema）](#7-数据格式规范json-schema)
8. [各指标采集方案](#8-各指标采集方案)
9. [网络质量评分算法](#9-网络质量评分算法)
10. [帧率采集方案](#10-帧率采集方案)
11. [日志系统](#11-日志系统)
12. [单实例与配置持久化](#12-单实例与配置持久化)
13. [开机自启动管理](#13-开机自启动管理)
14. [异常处理与降级策略](#14-异常处理与降级策略)
15. [性能兜底机制](#15-性能兜底机制)
16. [依赖清单与部署](#16-依赖清单与部署)
17. [目录结构规划](#17-目录结构规划)
18. [启动脚本与批处理](#18-启动脚本与批处理)
19. [UI 交互细节与边界场景补充](#19-ui-交互细节与边界场景补充)
20. [REST API 与 WebSocket 参考](#20-rest-api-与-websocket-参考)
21. [功能实现的理论效果](#21-功能实现的理论效果)
22. [扩展方向](#22-扩展方向)
23. [文档维护约定](#23-文档维护约定)
24. [自检脚本与验收](#24-自检脚本与验收)
25. [v5.0 迁移实施步骤](#25-v50-迁移实施步骤)

---

## 1. 项目概述

### 1.1 项目目标

构建一套运行于局域网（LAN）内的**硬件监控系统**，采用**前后端分离**架构：

- **副机端 Agent（服务端）**：运行在每台被监控电脑上的**后台服务**。每 1 秒采集本机硬件数据，作为 HTTP/WebSocket 服务端（端口 12345）等待连接；通过 WebSocket 向所有已订阅主机端**推送**实时数据；通过 REST API 提供节点/配置/健康/扫描等辅助能力。**可选**提供原生本机仪表盘（PyQt5）。
- **主机端 Host（纯前端）**：运行在主控电脑上的**原生桌面应用**（PyQt5，打包为独立 exe）。通过 WebSocket **订阅**所有 Agent，集中展示所有节点的实时详细数据；管理 Agent 地址列表、阈值变色、自定义红线告警。

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| **前后端分离** | Agent 只提供服务（采集 + API），Host 只做展示与交互（纯前端） |
| **标准协议** | 放弃 TCP 自定义帧 + UDP 广播主通道，改用 HTTP/REST + WebSocket |
| **多主机扩展** | 同一 Agent 可被多台 Host / 浏览器同时订阅（WebSocket 多客户端广播） |
| **数据帧兼容** | `monitor_data` JSON Schema 与 v4.0 完全一致，迁移不断档 |
| **节点自治** | 每台 Agent 独立运行，互不通信；单台离线不影响其他 |
| **局域网优先** | 1 秒高频推送，RTT 精度 < 1ms（WebSocket PING/PONG） |
| **健壮性** | 任意指标/连接失败均降级 N/A 或标记离线，不影响整体 |
| **异步非阻塞** | 采集、推送、GUI 刷新分离（Agent 用 asyncio，Host 用信号槽） |
| **运维友好** | 单实例检测、日志轮转、开机自启动、配置持久化 |
| **详细中文注释** | 全部代码含中文注释，方便二次修改 |

### 1.3 典型场景

- 机房多台服务器运行 Agent 后台服务（静默），运维主机集中监控所有节点；Agent 可选浏览器仪表盘供本机快速查看。
- 游戏主机运行 Agent，主控大屏集中显示各主机 CPU/GPU/FPS；选手可开 Agent 本机仪表盘自查。
- 多主机同时连接同一 Agent（如教练屏 + 运维屏 + 浏览器），互不影响。
- Host 端支持手动添加 Agent 地址，或通过 mDNS/连接码/.pcm/剪贴板便捷接入（§2.4）。

---

## 2. 角色与通信拓扑

### 2.1 角色

| 角色 | 程序 | 网络角色 | GUI | 说明 |
|------|------|----------|-----|------|
| **副机端 Agent** | `agent/`（`python -m agent`） | HTTP/WebSocket **Server (12345)** | 可选（本机仪表盘） | 采集 + 推送 + REST API + 节点管理 |
| **主机端 Host** | `host/`（`python -m host`） | HTTP/WebSocket **Client (多连接)** | 集中监控大屏 | 订阅所有 Agent，集中展示 |

### 2.2 通信拓扑

```
┌───────────────────────┐
│  副机端 A (Agent)      │
│  采集器 + WebSocket    │──┐
│  + REST API           │  │
│  本机仪表盘(可选)       │  │
└───────────────────────┘  │
                           ├── WebSocket (1s 推送) ──► 主机端 Host（订阅/展示）
┌───────────────────────┐  │   REST（健康/配置/扫描）
│  副机端 B (Agent)      │  │
│  采集器 + WebSocket    │──┘
│  + REST API           │
│  本机仪表盘(可选)       │
└───────────────────────┘

本机节点 (Host) ──本地采集器──→ Host 的"本机"卡片（可选，默认关闭，不经网络）
```

- 每个 Agent 独立采集、独立服务，可**同时服务多个客户端**（WebSocket 多订阅 + REST 多请求）。
- Agent 之间不直接通信；Host 通过配置的 Agent 地址列表分别连接。
- Host 的节点列表**本地持久化**（`host_config.json`），重启自动重连。

### 2.3 端口规划

| 用途 | 协议 | 默认端口 | 说明 |
|------|------|----------|------|
| HTTP + WebSocket | TCP | 12345 | Agent 监听（同一端口提供 `/api/*` 与 `/ws`） |
| UDP 自动发现（可选） | UDP | 12346 | Agent 广播心跳，Host 监听 |

> 端口需在 Windows 防火墙放行（专用网络）。详见 §16.2。

### 2.4 便捷连接方式（保留）

沿用 v4.0 的零配置接入能力，但**接入后通过 HTTP API 获取详细信息**：

| 方式 | 说明 |
|------|------|
| **mDNS 自动发现** | Agent 注册 `_pcmonitor._tcp.local.`，Host 自动发现并填入列表（§20.2） |
| **UDP 广播扫描** | Agent 每 2 秒广播 `agent_heartbeat`，Host 监听扫描（兼容层，§20.3） |
| **连接码** | 6 位纯数字短码（`ip:port:token` 摘要），Host 输入后经发现候选匹配（§20.4） |
| **.pcm 配置** | JSON 配置一键导入导出（§20.5） |
| **剪贴板** | `pcmonitor://<ip>:<port>?token=...` 连接串（§20.6） |
| **手动添加** | 输入 Agent 的 IP + 端口 + token（兜底） |

> 自动发现仅用于便捷添加入口；连接建立后一律走 HTTP/WebSocket 标准协议。

---

## 3. 系统架构设计

### 3.1 副机端 Agent 架构（服务端 · 异步）

```
┌────────────────────────────────────────────────────┐
│               副机端 Agent（服务端 · 异步）            │
│  ┌──────────────────────────────────────────────┐  │
│  │             采集层（线程池）                     │  │
│  │  CPU │ GPU │ 内存 │ 磁盘 │ 网络 │ 帧率 │ 进程 │ 系统 │
│  │  (各采集器独立线程，异常隔离，线程安全读取)         │  │
│  └───────────────────┬──────────────────────────┘  │
│                      │ get() 1s 节拍                │
│  ┌───────────────────▼──────────────────────────┐  │
│  │        数据聚合器 Aggregator（1 秒）            │  │
│  │   组装 monitor_data 帧 → 存入最新帧缓存          │  │
│  └───────┬─────────────────────┬────────────────┘  │
│  ┌───────▼────────────┐  ┌─────▼─────────────────┐ │
│  │ WebSocket Server    │  │ HTTP REST Server      │ │
│  │ ws://0.0.0.0:12345/ws│  │ http://0.0.0.0:12345 │ │
│  │ 多客户端订阅 · 每秒推送 │  │ /api/nodes /config   │ │
│  │ PING/PONG · 鉴权      │  │ /scan /health        │ │
│  └─────────────────────┘  └──────────────────────┘ │
│  ┌─────────────────────┐  ┌──────────────────────┐ │
│  │ 本机仪表盘（可选）     │  │ 自动发现（mDNS/UDP）   │ │
│  │ 本机仪表盘（可选，PyQt5） │  │ 广播 agent_heartbeat │ │
│  └─────────────────────┘  └──────────────────────┘ │
│  单实例互斥 · 日志 agent.log · 端口占用检测           │
└────────────────────────────────────────────────────┘
```

### 3.2 主机端 Host 架构（纯前端）

```
┌────────────────────────────────────────────────────┐
│           主机端 Host（纯前端 · 集中监控大屏）          │
│  ┌─────────────────────┐    ┌─────────────────────┐ │
│  │ 本地采集层（可选本机节点）│    │ 远程连接管理器          │ │
│  │ (复用 agent/collectors)│   │ dict[node_id]→AgentConnection │
│  └─────────┬───────────┘    │ 每节点独立 WS 连接+重连  │
│            │ 本机帧          └──────────┬───────────┘ │
│  ┌─────────▼───────────────────────────▼───────────┐ │
│  │      GUI 主线程（PyQt5 信号槽）                     │ │
│  │  左侧节点列表（别名/IP/状态/RTT/评分）              │ │
│  │  右侧详情面板（点击节点显示全部详细指标）             │ │
│  │  概览视图（手动切换 · 网格卡片）                    │ │
│  │  红线告警引擎（状态栏+日志+托盘弹窗）               │ │
│  └─────────────────────────────────────────────────┘ │
│  mDNS/UDP 监听 → 在线 Agent 列表 → 自动扫描弹窗（多选）  │
└────────────────────────────────────────────────────┘
```

### 3.3 线程/协程模型

| 单元 | 所属 | 职责 |
|------|------|------|
| 采集线程 ×N | Agent / Host 本机 | 各采集器独立线程，定时采集写共享数据 |
| 聚合线程 | Agent | 1 秒组装帧，写入最新帧缓存，触发 WS 广播 |
| asyncio 事件循环 | Agent | WebSocket Server（每连接协程）+ REST Server |
| WS 广播协程 | Agent | 每秒向所有已订阅客户端推送 `monitor_data` |
| 连接线程 ×N | Host | 每 Agent 一个，WS 连接 + 鉴权 + 接收 + 重连 |
| ping 协程/线程 ×N | Host | 每 Agent 一个，WS PING 帧测 RTT |
| 发现监听线程 | Agent / Host | 广播 / 监听心跳 |
| GUI 主线程 | Host | Qt 事件循环，信号槽更新界面 |

---

## 4. 通信协议设计（WebSocket + REST）

### 4.1 总览

放弃 TCP 长度前缀帧，改用**标准 WebSocket 消息**（文本 JSON）与 **HTTP JSON**：

| 通道 | 用途 | 说明 |
|------|------|------|
| **WebSocket** `/ws` | 实时推送监控数据 | Agent 每秒推送 `monitor_data` 帧；支持多客户端同时订阅 |
| **REST** `/api/*` | 辅助功能 | 节点列表、配置读写、健康检查、触发扫描 |
| **RTT 测量** | WebSocket PING/PONG 帧 | 标准 WS 控制帧，客户端本地时间戳计算 |

### 4.2 WebSocket 数据推送

- **连接**：`ws://<agent_ip>:12345/ws?token=xxx`（默认查询参数鉴权，§4.4）。
- **鉴权**：连接后 Agent 校验 token，失败关闭连接（HTTP 403 或 WS close 1008）。
- **推送**：鉴权通过后，Agent 每秒广播一条 `monitor_data` 文本帧（§7 Schema）。
- **多客户端**：Agent 维护订阅者集合，广播给所有已订阅客户端（与 v4.0 多显示端能力一致）。
- **RTT**：Host 端发 WS **PING 帧**，Agent 端由底层自动回 **PONG**（RFC 6455 控制帧），Host 用本地 `perf_counter` 时间戳计算 `RTT = (t_recv - t_sent) * 1000`，精度 < 1ms、无需时钟同步。

```python
# Agent 端：aiohttp + websockets 示意
async def ws_handler(ws):
    await auth(ws)                      # 首帧/查询参数校验 token
    subscribers.add(ws)
    try:
        async for msg in ws:            # 接收 PING 由底层自动回 PONG
            pass
    finally:
        subscribers.discard(ws)

async def push_loop():
    while True:
        frame = aggregator.latest_frame()            # 最新帧缓存
        for ws in list(subscribers):
            try: await ws.send_str(json.dumps(frame, ensure_ascii=False))
            except Exception: subscribers.discard(ws)
        await asyncio.sleep(1.0)
```

### 4.3 消息类型

| type | 方向 | 用途 | 说明 |
|------|------|------|------|
| `monitor_data` | Agent→Host | 1 秒监控数据帧 | Schema 见 §7（与 v4.0 一致） |
| `auth` | Host→Agent | 鉴权（首帧，若未走查询参数） | `{"type":"auth","token":"xxx"}` |
| `auth_result` | Agent→Host | 鉴权结果 | `{"ok":true}` / `{"ok":false,"reason":"token错误"}` |
| `agent_heartbeat` | Agent→局域网(UDP) | 自动发现心跳 | `hostname/ip/http_port/token/ts` |
| `loss_ping` / `loss_pong` | Host→Agent / Agent→Host | WS 链路丢包测量（低频，§4.7） | `{"seq":N,"ts":...}` |
| `error` | Agent→Host | 错误通知 | `{"code":..., "message":...}` |

### 4.4 鉴权流程

1. Agent 配置 `token`（默认随机生成或配置文件指定）。
2. Host 连接 `ws://ip:12345/ws` 时进行鉴权，**推荐方式：查询参数 `?token=xxx`**（默认/首选）。备选：连接后首帧发送 `{"type":"auth","token":"xxx"}`。
3. Agent 校验：匹配 → 加入订阅者集合并推送数据；不匹配 → 关闭连接（close 1008 / HTTP 403）。
4. REST 请求同理在 `Authorization: Bearer <token>` 头或 `?token=` 参数携带 token。

> **鉴权优先级（明确）**：推荐 **查询参数 `?token=xxx`** 作为默认鉴权方式——更简单、符合 RESTful 风格，且**在 WebSocket 握手阶段即可校验并拒绝**，无需等待首帧。**首帧 auth 消息作为备选**，用于不便修改 URL 的场景（如第三方客户端复用连接串、或需在连接建立后动态鉴权）。Agent 端实现需同时支持两者，Host 端默认走查询参数。
>
> token 明文传输，仅防误连，不防恶意（LAN 可信环境）。如需更强可加 TLS（自签名，见 §22）。

### 4.5 REST API（辅助）

| 方法 | 路径 | 用途 | 说明 |
|------|------|------|------|
| `GET` | `/api/health` | 健康检查 | `{"status":"ok","version":"5.0","uptime":...}` |
| `GET` | `/api/nodes` | 获取本机信息与已配置节点列表 | 返回本机概况 + 节点管理结果 |
| `POST` | `/api/scan` | 触发 UDP/mDNS 扫描 | 返回发现到的候选 Agent 列表 |
| `GET` | `/api/config` | 读取配置 | token 之外的配置（端口/采集开关/日志级别等） |
| `POST` | `/api/config` | 更新配置（别名等） | 见 §20.1 |

> 完整字段与示例见 §20。Host 端通过上述接口实现"节点管理"（添加、扫描、别名、持久化），替代 v4.0 中副机端 GUI 直连操作。

### 4.6 超时与重连

- 每 Agent 连接独立设置 WS 超时（如 30 秒无消息则视为断开）。
- 断线后**每 Agent 独立**指数退避重连：1s→2s→4s→8s→16s→32s→60s 封顶；连上后重置为 1s。
- 已配置的 Agent 即使离线也保留在列表中，持续重连（见 §19.7）。

### 4.7 丢包测量

- **到网关丢包（主）**：`net_quality.packet_loss_percent` 默认由**到网关丢包**（系统 `ping` 解析）承担，免提权、兼容中英文输出。
- **WS 链路丢包（补充，保留）**：标准 WebSocket 是可靠传输，天然无应用层丢包；但为感知"中间链路质量"（如交换机拥塞丢包），**保留低频应用层 `loss_ping`/`loss_pong` 作为补充测量**：
  - Host 每 **10 秒**发 3 个 `{"type":"loss_ping","seq":N,"ts":...}`（间隔 100ms），Agent 回 `{"type":"loss_pong","seq":N,"ts":...}`。
  - 1 秒后统计：`WS链路丢包率 = (3 - 已收 loss_pong 数) / 3 * 100%`。
  - 该值可作为独立指标展示，或与网关丢包综合纳入评分（§9）。
- **设计取舍（明确）**：若不需要中间链路质量感知，可仅保留网关丢包；WS 链路丢包为**可选增强**，默认开启低频测量，开销可忽略。

---

## 5. 副机端设计（Agent · 服务端）

### 5.1 启动流程

```
1. 解析命令行参数（--install-startup / --remove-startup / 普通启动）
2. 单实例检测（命名互斥体 Global\PC_Monitor_Agent），已有实例则退出
3. 初始化日志（RotatingFileHandler → logs/agent.log）
4. 加载配置 agent_config.json（v4.0 node_config.json 迁移）
5. 端口占用检测（TCP 12345 / UDP 12346），占用则提示并退出
6. 初始化各采集器（CPU/GPU/内存/磁盘/网络/帧率/进程/系统/网络质量）
7. 启动采集线程池
8. 启动数据聚合定时器（1 秒节拍 → 最新帧缓存）
9. 启动 HTTP REST Server（0.0.0.0:12345，/api/*）
10. 启动 WebSocket Server（/ws，多订阅推送）
11. 启动 UDP/mDNS 广播器（可选，自动发现）
12. 【可选】启动本机仪表盘（原生 PyQt5 界面）
13. 进入 asyncio 事件循环（Event.wait 阻塞，等退出信号）
```

> **运行方式（开发 vs 生产）**：
> - **开发调试**：`python -m agent` —— 有控制台窗口，可直接观察 stdout/日志。
> - **生产部署**：`pythonw -m agent`（无控制台窗口，纯后台）或注册为 Windows 服务（见 §22）。
> - `pythonw.exe` 会丢弃 stdout/stderr，调试困难，故仅用于生产。

### 5.2 采集器接口

沿用 v4.0 设计，各采集器独立线程、异常隔离、线程安全读取：

```python
class BaseCollector:
    """采集器基类：独立线程、异常隔离、线程安全读取"""
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self._lock = threading.Lock()
        self._data = {}
        self._stop = threading.Event()

    def start(self):
        t = threading.Thread(target=self._loop, daemon=True,
                             name=self.__class__.__name__)
        t.start()

    def _loop(self):
        try:
            self._data = self.collect()          # 首次预热
        except Exception as e:
            logging.warning(f"{self.__class__.__name__} 首次采集失败: {e}")
        while not self._stop.is_set():
            try:
                result = self.collect()
                with self._lock:
                    self._data = result
            except Exception as e:
                logging.warning(f"{self.__class__.__name__} 采集失败: {e}")
            self._stop.wait(self.interval)

    def collect(self) -> dict:
        raise NotImplementedError

    def get(self) -> dict:
        with self._lock:
            return dict(self._data)
```

### 5.3 数据聚合器

```python
class DataAggregator:
    """每 1 秒聚合数据，写入最新帧缓存；WS 推送协程从缓存读取广播"""
    def __init__(self, collectors):
        self.collectors = collectors
        self._latest = {}          # 最新帧缓存（线程安全）
        self._lock = threading.Lock()

    def latest_frame(self) -> dict:
        with self._lock:
            return dict(self._latest)

    def _loop(self):
        while True:
            frame = {
                "type": "monitor_data",
                "ts": time.time(),
                "hostname": socket.gethostname(),
                "cpu": self.collectors["cpu"].get(),
                "ram": self.collectors["ram"].get(),
                "gpu": self.collectors["gpu"].get(),
                "disk": self.collectors["disk"].get(),
                "net": self.collectors["net"].get(),
                "net_quality": self.collectors["net_quality"].get(),
                "fps": self.collectors["fps"].get(),
                "processes": self.collectors["proc"].get(),
                "system": self.collectors["sys"].get(),
                "connected_clients": ws_server.subscriber_count(),
            }
            with self._lock:
                self._latest = frame
            time.sleep(self.interval)
```

### 5.4 本机仪表盘（可选，已实现）

- **方案 A（原生 PyQt5 GUI，已实现）**：PyQt5 界面，仅用于显示本机数据——本地采集数据直接喂给 GUI（`agent/gui/`，复用 `DetailPanel`），**不再连接远程节点**（节点管理已移到 Host）。
- **方案 B（本地 Web，不推荐）**：Agent 内嵌 HTTP 页面（`http://<ip>:12345/`），浏览器访问查看本机仪表盘。

> **采用方案 A（原生 PyQt5）**，理由：
> 1. **与整体技术栈一致**——Host 也是 PyQt5 桌面程序，两端统一为原生 exe，维护心智成本低；
> 2. **无需依赖浏览器/HTTP 页面**——仪表盘直接走 Qt 信号槽复用本地采集数据，不经网络，与推送数据同构；
> 3. **打包统一**——Agent 与 Host 都用 PyInstaller 打 exe，符合 §16.5 双端独立打包约束。
>
> **使用方式**：`python -m agent --gui`（Qt 主循环 + 后台 asyncio 服务同进程，关闭窗口即停服务）；默认 `python -m agent` 为无界面后台模式（pythonw 运行）。
> 方案 B 作为备选（未来若需远程浏览器查看本机指标时启用）。两种方案均复用 `agent/collectors/`，与推送数据同构。

### 5.5 配置管理

保留 `agent_config.json`，字段含 token、端口、采集器开关、日志级别等（§12.2）。

### 5.6 开机自启 / 单实例

- **开机自启**：Windows 沿用 schtasks（Agent 需管理员，`/RL HIGHEST`）；Linux 用 systemd（若跨平台）。
- **单实例**：命名互斥体 `Global\PC_Monitor_Agent`（§12.1）。

---

## 6. 主机端设计（Host · 纯前端）

### 6.1 概述

Host 端作为**纯前端应用**，通过 WebSocket 订阅所有 Agent，集中展示数据。

| 功能 | 说明 |
|------|------|
| **节点列表（左侧）** | 显示所有已配置/已连接 Agent（别名、IP、状态、RTT、评分） |
| **详情面板（右侧）** | 点击节点显示该节点全部详细指标，阈值变色 |
| **概览视图** | 网格卡片布局，关键指标一目了然（适合大屏） |
| **红线告警** | 自定义红线检测 + 状态栏/日志/托盘弹窗（§第四篇） |
| **节点管理** | 通过 REST API 添加/扫描/改别名；配置持久化到 `host_config.json` |
| **本机节点（可选，默认关闭）** | 复用采集器本地采集，作为"本机"卡片显示；默认关闭，用户手动启用 |

### 6.2 前端技术选型

| 方案 | 说明 |
|------|------|
| **原生 PyQt5 + WebSocket 客户端（采用）** | 迁移成本最低，沿用现有 GUI 与 QSS 深色主题；替换 `host/connection.py` 的 TCP 为 WS；打包为独立 exe |
| **Electron + Vue/React（不采用，备选）** | 未来若需 Web 化再考虑；需重写 GUI，与现有 PyQt5 大量代码不兼容 |

> **技术决策（明确）**：Host 端采用**原生 PyQt5 桌面应用**，网络层统一为"WebSocket 客户端 + REST 客户端"，GUI 层仅消费数据帧。Electron/Web 方案**不在本版本实施范围**，仅作为未来扩展方向保留。

### 6.3 WebSocket 客户端

```python
class AgentConnection(QObject):
    """单个 Agent 的连接：WS 接收 + 重连 + RTT + 信号"""
    data_received = pyqtSignal(dict, str)       # (frame, node_id)
    status_changed = pyqtSignal(str, str)       # (node_id, status_text)
    rtt_updated = pyqtSignal(float, str)        # (rtt_ms, node_id)

    def connect_ws(self, ip, port, token):
        # websocket-client / aiohttp 建立 ws://ip:port/ws?token=xxx
        # 接收 monitor_data 帧 → emit data_received
        # 定期发 WS PING → 计算 RTT
        ...
```

### 6.4 节点管理（经 REST API）

- **手动添加**：输入 Agent 的 IP + 端口 + 别名 + token，经 `GET /api/health` 校验可达后写入列表。
- **自动扫描**：点击"扫描"→ 触发 `POST /api/scan` 或本地 UDP/mDNS 监听 → 弹窗多选批量添加。
- **别名/配置**：`POST /api/config` 更新远端别名等；Host 本地列表可编辑别名（仅本地生效）。
- **持久化**：Agent 列表（IP/端口/别名/token）、窗口布局、视图模式保存到 `host_config.json`。

### 6.5 展示功能（沿用 v4.0）

- 节点列表项：别名 / IP / 状态（● 在线 ● 重连中 ● 离线 / 鉴权失败）/ RTT / 评分（§19.1）。
- 详情面板：全部指标分区显示，阈值三级变色（§14.1）。
- 概览视图：网格卡片（CPU/GPU/内存/温度/FPS/评分），上限可配，横向滚动（§19.2）。
- 顶部状态栏：已连接节点数 / 总节点数。
- 窗口关闭确认；最小化不退出，后台连接继续（§19.8）。

> **本机节点定位（明确）**：Host 的"本机节点"是一个**可选的辅助功能**，**默认关闭**，仅在用户手动启用时才在 Host 本地启动采集器并显示为一张卡片。它**不影响主架构**——Host 核心职责仍是纯前端（订阅/展示/告警），本机节点只是让"监控机本身"也能被纳入监控。启用后数据来自本地采集器（不经网络），与远程节点同构显示。若追求严格的"前后端分离"、不需要监控 Host 本身，可保持关闭，功能不受任何影响。

---

## 7. 数据格式规范（JSON Schema）

每秒推送的完整数据帧（`type: monitor_data`）——**与 v4.0 完全一致**：

```json
{
  "type": "monitor_data",
  "ts": 1722892800.123,
  "hostname": "GAME-PC",
  "connected_clients": 2,

  "system": {
    "uptime_seconds": 86400,
    "local_ip": "192.168.1.100"
  },

  "cpu": {
    "name": "Intel Core i7-7700K",
    "total_usage": 45.2,
    "per_core_usage": [30.1, 52.3, 40.0, 58.5],
    "physical_cores": 4,
    "logical_cores": 8,
    "core_freq_mhz": 4200,
    "package_temp_c": 65.0,
    "power_w": 85.0
  },

  "ram": {
    "total_gb": 32.0,
    "used_gb": 16.0,
    "available_gb": 16.0,
    "usage_percent": 50.0,
    "swap_used_mb": 512.0
  },

  "gpu": {
    "name": "NVIDIA GeForce RTX 3070",
    "usage_percent": 62.0,
    "vram_used_mb": 4096,
    "vram_total_mb": 8192,
    "vram_usage_percent": 50.0,
    "core_temp_c": 68.0,
    "mem_temp_c": "N/A",
    "hotspot_temp_c": 75.0,
    "core_freq_mhz": 1800,
    "mem_freq_mhz": 7000,
    "power_w": 120.0,
    "power_limit_w": 250.0,
    "engine_usage": {"graphics":62.0,"compute":5.0,"encode":0.0,"decode":0.0},
    "top_vram_processes": [
      {"name":"game.exe","vram_mb":2048},
      {"name":"chrome.exe","vram_mb":512},
      {"name":"discord.exe","vram_mb":256}
    ]
  },

  "disk": [
    {"drive":"C:","read_mb_s":120.5,"write_mb_s":45.2,
     "read_iops":1500,"write_iops":800,"queue_depth":1.2,
     "temp_c":"N/A","free_gb":200.0,"total_gb":500.0,"usage_percent":60.0}
  ],

  "net": {
    "interface":"以太网",
    "upload_mb_s":1.2,"download_mb_s":5.6,
    "link_speed_mbps":1000,
    "errors_sent":0,"errors_recv":0,"drops_sent":0,"drops_recv":0
  },

  "net_quality": {
    "latency_to_client_ms": null,
    "latency_to_gateway_ms":2.1,
    "packet_loss_percent":0.0,
    "quality_score":98,
    "quality_grade":"优秀"
  },

  "fps": {
    "window_title":"Cyberpunk 2077",
    "fps":142,"frame_time_ms":7.0,"low_1_percent":98,
    "source":"presentmon"
  },

  "processes": {
    "top_cpu":[{"name":"chrome.exe","usage_percent":12.0},
               {"name":"game.exe","usage_percent":8.0},
               {"name":"Code.exe","usage_percent":5.0}],
    "top_gpu":[{"name":"game.exe","usage_percent":65.0},
               {"name":"chrome.exe","usage_percent":5.0},
               {"name":"discord.exe","usage_percent":2.0}]
  }
}
```

> 无法获取的字段统一 `"N/A"` 或 `null`，GUI 识别后显示 N/A 并跳过变色。
> **`net_quality.latency_to_client_ms`**：Agent 端填 `null`，RTT 由各 Host 本地经 WebSocket PING 测量，带 node_id（见 §19.5）。

---

## 8. 各指标采集方案

> 采集方案对 Agent 与 Host 本机节点**完全一致**（共享 `common/collectors/`，由原 `node/collectors/` 迁移）。

### 8.1 CPU

| 指标 | 方案 | 库 |
|------|------|-----|
| 总/每核使用率 | `psutil.cpu_percent(percpu=True)` | psutil |
| 频率 | `psutil.cpu_freq()` / WMI | psutil |
| 温度/功耗 | LibreHardwareMonitor (WMI) | 需管理员 |
| 核心数 | `psutil.cpu_count(logical=False/True)` | psutil |
| 型号 | `cpuinfo.get_cpu_info()['brand_raw']` | py-cpuinfo |

### 8.2 内存

`psutil.virtual_memory()` + `psutil.swap_memory()`，最稳定。

### 8.3 GPU

GPU 采集按厂商分三路，优先级 NVIDIA > AMD > Intel，任一可用即返回真实数据，全部不可用则返回全 N/A（保证 §7 Schema 字段完整）。

#### 8.3.1 NVIDIA（pynvml / NVML，主方案）

**库**：`nvidia-ml-py`（PyPI 包名，`import pynvml`）。NVML 随 NVIDIA 驱动自带 `nvml.dll`，**无需单独装 CUDA Toolkit**。要求 NVIDIA 驱动 ≥ R341 分支（350+）。

```python
import pynvml
pynvml.nvmlInit()                                # 启动一次
handle = pynvml.nvmlDeviceGetHandleByIndex(0)    # 单 GPU（index=0）
# ... 周期采集期间复用 handle ...
pynvml.nvmlShutdown()                            # 退出一次
```

`nvmlInit()` 失败（非 N 卡 / 驱动未装 / NVML 库缺失）捕获 `pynvml.NVMLError`，采集器整体降级为全 N/A。

**字段 → NVML API 映射**（对照 §7 `gpu` 字段）：

| JSON 字段 | NVML API | 说明 / 单位换算 |
|-----------|----------|----------------|
| `name` | `nvmlDeviceGetName(handle)` | bytes/str 需统一处理 |
| `usage_percent` | `nvmlDeviceGetUtilizationRates(handle).gpu` | 已是百分比 |
| `vram_used_mb` | `nvmlDeviceGetMemoryInfo(handle).used / 1024**2` | 字节→MB |
| `vram_total_mb` | `nvmlDeviceGetMemoryInfo(handle).total / 1024**2` | 字节→MB |
| `vram_usage_percent` | `round(used / total * 100, 1)` | 自算 |
| `core_temp_c` | `nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)` | 摄氏度 |
| `mem_temp_c` | `nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_MEMORY)` | 部分卡不支持→N/A |
| `hotspot_temp_c` | `nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU_HOTSPOT)` | 部分卡不支持→N/A；否则用 LibreHardwareMonitor 补 |
| `core_freq_mhz` | `nvmlDeviceGetClockInfo(handle, NVML_CLOCK_GRAPHICS)` | MHz |
| `mem_freq_mhz` | `nvmlDeviceGetClockInfo(handle, NVML_CLOCK_MEM)` | MHz |
| `power_w` | `nvmlDeviceGetPowerUsage(handle) / 1000.0` | 毫瓦→瓦 |
| `power_limit_w` | `nvmlDeviceGetEnforcedPowerLimit(handle) / 1000.0` | 毫瓦→瓦 |
| `engine_usage.graphics` | `nvmlDeviceGetUtilizationRates(handle).gpu` | 与 usage_percent 同源 |
| `engine_usage.encode` | `nvmlDeviceGetEncoderUtilization(handle)` | 返回 `(utilization%, sampling_period_us)`，取第一项 |
| `engine_usage.decode` | `nvmlDeviceGetDecoderUtilization(handle)` | 同上 |
| `top_vram_processes` | `nvmlDeviceGetComputeRunningProcesses(handle)` | 见 §8.3.4 |

> **热点温度 API 可用性**：`NVML_TEMPERATURE_GPU_HOTSPOT` 在**旧版 nvidia-ml-py 中可能未定义**（需 Driver 435+ / 对应 NVML 版本）。
> 实现时**必须做属性存在性 fallback**：用 `getattr(pynvml, "NVML_TEMPERATURE_GPU_HOTSPOT", None)` 判断，若枚举不存在、调用抛 `NVMLError`/`AttributeError` 或不支持，则 `hotspot_temp_c` 返回 `"N/A"`，**不因单 API 缺失导致整个 GPU 采集失败**。
>
> **热点温度回退链路**：热点温度优先使用 NVML；若不可用，则回退到 LibreHardwareMonitor WMI 读取（见 `common/lhm.py`，需管理员），再不可用才返回 `"N/A"`。
> **依赖关系**：`common/lhm.py` 是 `cpu_collector.py`（CPU 温度/功耗）与 `gpu_collector.py`（GPU 热点温度补读）的**共享依赖模块**。

> **多 GPU**：`pynvml.nvmlDeviceGetCount()` 遍历枚举。默认采集 `index=0`（主渲染卡），配置项 `gpu_index`（agent_config.json）可指定。

#### 8.3.2 AMD（pyadl，后备方案）

**库**：`pyadl`（基于 ADL/ADLX SDK）。**支持范围有限**，仅以下字段可取真实值，其余 N/A：

| 可采集字段 | API |
|-----------|-----|
| `name` | `ADLManager.getInstance().getDevices()[i].getName()` |
| `usage_percent` | `device.getCurrentUsage()` |
| `core_temp_c` | `device.getCurrentTemperature()` |
| `core_freq_mhz` / `mem_freq_mhz` | `device.getCurrentEngineClock()` / `getCurrentMemoryClock()` |

**不支持**：显存占用、显存进程、功耗/功耗墙、引擎细分、显存温度、热点温度 → 统一 N/A。

#### 8.3.3 Intel（集显，降级）

Intel 集显无免费稳定的 Python 采集库。返回全 N/A，仅 `name` 通过 WMI `Win32_VideoController.Name` 取得。

#### 8.3.4 GPU Top3 进程（→ `processes.top_gpu`）

仅 NVIDIA 可用：`nvmlDeviceGetComputeRunningProcesses(handle)` 返回占用 GPU 显存的进程列表，每项含 `pid` 与 `usedGpuMemory`（字节）。

> **关键健壮性**：新版 `nvidia-ml-py`（≥13）在无法获取某进程显存占用时，`p.usedGpuMemory` 返回 **`None`** 而非抛异常。**必须判空**，否则 `None / 1024**2` 抛 `TypeError` 会导致整个 GPU 采集失败。

```python
for p in procs:
    if p.usedGpuMemory is None:   # → 必须判空跳过
        continue
    vram_mb = round(p.usedGpuMemory / (1024 ** 2))
    ...
```

PID → `psutil.Process(pid).name()` 取进程名，按显存降序取 Top3。AMD/Intel 卡 `top_gpu` 返回空列表 `[]`。

### 8.4 磁盘

- 读写速度/IOPS：`psutil.disk_io_counters` 1 秒差分。
- **盘符↔物理盘映射**：WMI `Win32_DiskDriveToDiskPartition` + `Win32_LogicalDiskToPartition`。
- 队列深度：Performance Counter `\PhysicalDisk\Current Disk Queue Length`（**docstring 需用 raw string `r"""..."""` 避免 `\P` 转义警告**）。
- 温度：LibreHardwareMonitor / smartctl（需管理员）。
- 剩余空间/使用率：`psutil.disk_usage`。

### 8.5 网络

`psutil.net_io_counters(pernic=True)` 差分；网卡链接速度 WMI `Win32_NetworkAdapter.Speed`；错误/丢弃包计数取 `errin/errout/dropin/dropout`。

### 8.6 网络质量

- 到各 Host RTT：见 §4.4（各 Host 独立经 WebSocket PING 测量，带 node_id）。
- 到网关延迟：解析系统 `ping` 输出（兼容中英文），免提权。
- 丢包率：见 §4.7。
- 评分：见 §9，**滑动平均**（最近 N 次评分均值，平滑抖动）。

### 8.7 进程（2~3 秒采集，与 1 秒数据帧解耦）

- CPU Top3：`psutil.process_iter` 排序（需预热）。
- GPU Top3：NVML 取 PID + 占用（注意 §8.3.4 判空）。
- uptime：`time.time() - psutil.boot_time()`。

### 8.8 帧率

见 §10。前台窗口动态绑定。

## 9. 网络质量评分算法

### 9.1 评分公式

```
延迟扣分 = max(0, (rtt_ms - 5) / 10) * 5      # 5ms 起算，每增 10ms 扣 5 分
丢包扣分 = packet_loss_percent * 10             # 每 1% 丢包扣 10 分
瞬时分   = max(0, round(100 - 延迟扣分 - 丢包扣分))
```

> **系数说明**：延迟扣分系数为 **5**，与 v2.0/v3.0/v4.0 保持一致，避免延迟惩罚过重。
> （v3.0 曾采用系数 15，导致 rtt=15ms 即扣 15 分、评分 85 仅"良好"，延迟惩罚偏重，故回退为 5。）

**瞬时分校验**（应与 §9.3 等级一致）：

| rtt_ms | loss% | 延迟扣分 | 丢包扣分 | 瞬时分 | 等级 |
|--------|-------|---------|---------|--------|------|
| 1 | 0 | 0 | 0 | 100 | 优秀 ✓ |
| 15 | 0 | 5 | 0 | 95 | 优秀 ✓ |
| 30 | 1 | 12.5 | 10 | 78 | 良好 ✓ |
| 5 | 8 | 0 | 80 | 20 | 较差 ✓ |

### 9.2 滑动平均（平滑抖动）

```python
from collections import deque
class QualityScorer:
    def __init__(self, window=10):
        self.scores = deque(maxlen=window)
    def update(self, rtt_ms, loss_percent):
        latency_pen = max(0, (rtt_ms - 5) / 10) * 5
        loss_pen = loss_percent * 10
        instant = max(0, round(100 - latency_pen - loss_pen))
        self.scores.append(instant)
        score = round(sum(self.scores) / len(self.scores))
        grade = ("优秀" if score>=90 else "良好" if score>=70
                 else "一般" if score>=50 else "较差")
        return score, grade
```

> **滑动窗口说明**：显示分 = 最近 N 次瞬时分均值，平滑无线网络抖动。**单元测试评估各档等级时，应使用独立的新建 scorer**（避免前序样本污染均值）；一次性恶值不剧变用单独用例验证平滑效果。

### 9.3 等级

| 评分 | 等级 | 颜色 |
|------|------|------|
| ≥90 | 优秀 | 绿 |
| 70~89 | 良好 | 青绿 |
| 50~69 | 一般 | 橙 |
| <50 | 较差 | 红 |

---

## 10. 帧率采集方案

### 10.1 方案对比与选择

| 方案 | 原理 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|---------|
| **PresentMon CLI**（主） | ETW 捕获 Present 调用 | 精准官方级，支持全屏独占 | 需下载 exe / 管理员 / 分发许可 | 有 PresentMon.exe 且有管理员权限 |
| **DXGI 截帧**（降级） | dxcam 桌面帧差分估计 | 纯 Python，零外部 exe | 全屏独占可能失败；占少量 GPU | 无 PresentMon 或无管理员权限 |

**选择逻辑**（采集器启动时）：

1. 配置 `collectors.fps` 为 `"presentmon"` 或默认：检测 `tools/PresentMon.exe` 存在 **且** 进程有管理员权限 → 用 PresentMon
2. `tools/PresentMon.exe` 不存在或非管理员 → **自动降级 DXGI**
3. `collectors.fps == "dxgi"`：强制 DXGI
4. `collectors.fps == false`：不采集，返回 N/A（`source: "none"`）

> **降级日志提示（明确）**：当 **有管理员权限但 `tools/PresentMon.exe` 未找到** 时（步骤 2 命中），
> 采集器应记录一条 **INFO 日志**：
> `"PresentMon.exe 未找到，已自动降级为 DXGI 截帧模式，如需更精准帧率请下载 PresentMon.exe 放入 tools/ 目录"`
>
> **dxcam 降级提示**：DXGI 模式下若 `dxcam` 未安装（`pip install dxcam` 可启用），帧率返回 N/A，
> 采集器**每个进程仅警告一次**（模块级标志），避免重复刷屏（§19.9）。

### 10.2 前台窗口动态绑定

```python
import win32gui, win32process
def get_foreground_process_name():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    title = win32gui.GetWindowText(hwnd)
    try:
        name = psutil.Process(pid).name()
    except Exception:
        name = "N/A"
    return name, title
```

PresentMon 按 `process_name` 捕获。采集器每秒检测前台进程名，**变化时**停止旧 PresentMon 会话、按新进程名重启（§10.4），实现窗口切换自动重新绑定。

### 10.3 PresentMon CLI 调用

**命令行**（PresentMon 2.x，参数单横杠）：

```
PresentMon.exe -process_name <前台进程名> -output_stdout -no_top -stop_existing_session -session_name PCMonitor
```

| 参数 | 作用 |
|------|------|
| `-process_name` | 仅捕获指定进程（按 §10.2 前台窗口绑定） |
| `-output_stdout` | CSV 实时写到 stdout，采集器读管道解析（避免磁盘 IO） |
| `-no_top` | 不显示控制台 swap chain 列表，减少输出噪音 |
| `-stop_existing_session` | 启动时若已有同名 ETW 会话则先停掉，避免"会话已存在"错误 |
| `-session_name PCMonitor` | 自定义 ETW 会话名，与其他性能工具共存 |

**关键 CSV 字段**（逐行解析最新数据行）：

| 字段 | 含义 | 用途 |
|------|------|------|
| `msBetweenPresents` | 两次 Present 间隔（毫秒） | `fps = 1000 / msBetweenPresents` |
| `Dropped` | 是否丢帧（0/1） | 丢帧统计 |
| `msGPUActive` | GPU 渲染该帧耗时 | GPU 帧耗时 |
| `Application` / `ProcessID` | 进程名 / PID | 校验绑定目标 |

### 10.4 PresentMon 进程管理

```python
import subprocess, threading
class PresentMonSession:
    def start(self, process_name):
        self.proc = subprocess.Popen(
            ["tools/PresentMon.exe", "-process_name", process_name,
             "-output_stdout", "-no_top", "-stop_existing_session",
             "-session_name", "PCMonitor"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW)
        threading.Thread(target=self._read_loop, daemon=True).start()

    def _read_loop(self):
        for line in self.proc.stdout:
            self._parse_csv_line(line)

    def stop(self):
        if self.proc:
            self.proc.terminate()
            try: self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired: self.proc.kill()
```

**重启 / 崩溃处理**：前台进程名变化 → `stop()` + `start(new_name)`；子进程意外退出 → 日志 WARNING，指数退避重启（1s→10s）。无权限时自动降级 DXGI。

### 10.5 DXGI 截帧降级实现

**库**：`dxcam`（高性能 DXGI 桌面捕获，纯 pip 安装，**仅 Windows**）。配合 `numpy` 做帧差分。

```python
import dxcam, numpy as np, time
from collections import deque
class DxFpsEstimator:
    def __init__(self, threshold=0.02):
        self.camera = dxcam.create(output_color="GRAY")
        self.prev = None
        self.threshold = threshold
        self.frame_times = deque(maxlen=100)

    def sample(self):
        frame = self.camera.grab()
        if frame is None or self.prev is None:
            self.prev = frame; return None
        diff = np.mean(np.abs(frame.astype(int) - self.prev.astype(int)) > 8)
        if diff > self.threshold:
            self.frame_times.append(time.perf_counter())
        self.prev = frame
```

**局限**：全屏独占下 `grab()` 返回黑屏 → FPS 失败（返回 N/A）；多显示器默认主显示器。

### 10.6 1% Low 计算

最近 100 帧帧时间排序，取第 99 百分位 → `low_1_percent = 1000 / frame_time_p99`。

```python
class FrameStats:
    def __init__(self):
        self.frame_times = deque(maxlen=100)
    def push(self, ms): self.frame_times.append(ms)
    def fps(self):
        return round(1000 / np.mean(self.frame_times), 1) if self.frame_times else "N/A"
    def low_1(self):
        if len(self.frame_times) < 10: return "N/A"
        p99 = np.percentile(list(self.frame_times), 99)
        return round(1000 / p99, 1)
```

### 10.7 采集间隔与数据帧同步

帧率采集是**事件驱动**（PresentMon 持续输出 / DXGI 轮询 100ms），与 1 秒数据帧解耦：采集器内部维护 `FrameStats`（最近 100 帧滑动窗口），聚合器每 1 秒取快照。`source` 字段标注：`"presentmon"` / `"dxgi"` / `"none"`。

### 10.8 配置项

`agent_config.json` 中：

```json
"collectors": {
  "fps": "presentmon",      // "presentmon"(默认) | "dxgi" | false
  "gpu": true,
  "temperature": true
}
```

> Host 端本机节点同样支持帧率采集（前台窗口绑定本机前台进程）。

---

## 11. 日志系统

### 11.1 配置

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
    return logger
```

### 11.2 日志级别可配置

- 默认 **INFO**；配置文件增加 **`log_level`** 字段（`agent_config.json` / `host_config.json` 通用），取值 `"DEBUG" / "INFO" / "WARNING" / "ERROR"`。
- 示例：`"log_level": "DEBUG"` 用于排查连接/协议问题；生产环境保持 `"INFO"` 或 `"WARNING"`。
- 未配置时默认 `"INFO"`。

### 11.3 日志文件

| 端 | 文件 | 说明 |
|----|------|------|
| 副机端 Agent | `logs/agent.log` | 采集器/WS/REST/广播器日志 |
| 主机端 Host | `logs/host.log` | 所有 Agent 连接日志，带 `node_id`/`alias` 标签 |

```python
# 每 Agent 连接日志带标签
self.log = logging.getLogger(f"host.node.{self.node_id[:8]}")
self.log.info(f"{self.alias} 已连接")
```

---

## 12. 单实例与配置持久化

### 12.1 单实例检测

Windows 命名互斥体（`pywin32`）：

```python
import win32event, win32api, winerror
def ensure_single_instance(name):
    mutex = win32event.CreateMutex(None, False, name)
    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
        return None  # 已有实例
    return mutex  # 保持引用防止释放
```

- 副机端 Agent：`name="Global\\PC_Monitor_Agent"`
- 监控主机 Host：`name="Global\\PC_Monitor_Host"`

已有实例则提示并退出，避免端口/资源冲突。

> **双端共存（§16.5.3）**：Agent 与 Host 的互斥体名不同，**允许在同一台电脑上同时运行**——此时该电脑既是被监控机（Agent 后台服务）也是监控机（Host 前台大屏），互不干扰。

### 12.2 配置持久化

**副机端 `agent_config.json`**（由 v4.0 `node_config.json` 迁移）：

```json
{
  "http_port": 12345,
  "udp_port": 12346,
  "token": "auto_generated_or_custom",
  "use_multicast": false,
  "preferred_iface": "",                 // 指定网卡名，空则自动选取
  "gpu_index": 0,                        // 多卡时指定
  "log_level": "INFO",                   // 日志级别（§11.2）
  "collectors": {"fps": "presentmon", "gpu": true, "temperature": true}
}
```

**监控主机 `host_config.json`**：

```json
{
  "hosts": [
    {"node_id":"a1b2c3","ip":"192.168.1.100","port":12345,
     "token":"abc","alias":"游戏主机"}
  ],
  "window_geometry": {"x":100,"y":100,"w":1400,"h":900},
  "view_mode": "auto",                   // auto/single/multi/overview
  "max_overview_cards": 16,              // 概览模式最大卡片数
  "max_cards_per_row": 4,                // 每行卡片数
  "udp_port": 12346,                     // 心跳监听端口（可选发现）
  "log_level": "INFO",                   // 日志级别（§11.2）
  "gui_refresh_interval": 1.0,           // GUI 刷新间隔秒（§19.8，预留）
  "alert_popup": true,                   // 红线告警托盘弹窗开关（第四篇）
  "language": "zh_CN",                   // 界面语言（第三篇）
  "last_selected_node": "a1b2c3"
}
```

> Host 端保存 Agent 列表（IP/端口/别名/token）、窗口布局、视图模式、告警配置、语言。
> `node_id` 生成：`hashlib.md5(f"{ip}:{port}".encode()).hexdigest()[:8]`；本机节点固定 `node_id="localhost"`。

---

## 13. 开机自启动管理

### 13.1 命令行参数

| 程序 | 参数 | 作用 |
|------|------|------|
| `agent/`（`python -m agent`） | `--install-startup` | 安装 Agent 开机自启（需管理员） |
| `agent/`（`python -m agent`） | `--remove-startup` | 卸载 Agent 开机自启 |
| `host/`（`python -m host`） | `--install-startup` | 安装 Host 开机自启（无需管理员） |
| `host/`（`python -m host`） | `--remove-startup` | 卸载 Host 开机自启 |

### 13.2 副机端 Agent：schtasks 计划任务（需管理员）

```python
def install_agent_startup():
    exe = sys.executable.replace("python.exe", "pythonw.exe")  # 无控制台窗口
    script = os.path.abspath("agent/__main__.py")
    cmd = f'"{exe}" "{script}"'
    subprocess.run([
        "schtasks", "/Create", "/TN", "PC_Monitor_Agent",
        "/TR", f'"{cmd}"',
        "/SC", "ONLOGON",      # 登录时触发
        "/RL", "HIGHEST",      # 最高权限（满足温度/帧率采集）
        "/F"
    ], check=True)
```

> `/RL HIGHEST` 使计划任务以管理员权限静默运行，满足 LibreHardwareMonitor/PresentMon 的提权需求；`pythonw.exe` 保证无控制台窗口弹出。

### 13.3 监控主机 Host：注册表 Run 项（无需管理员）

```python
import winreg
def install_host_startup():
    exe = sys.executable.replace("python.exe", "pythonw.exe")
    script = os.path.abspath("host/__main__.py")
    key = winreg.HKEY_CURRENT_USER
    sub = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(key, sub, 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, "PC_Monitor_Host", 0, winreg.REG_SZ, f'"{exe}" "{script}"')
```

### 13.4 卸载

- Agent：`schtasks /Delete /TN PC_Monitor_Agent /F`
- Host：删除注册表 `Run` 项下的 `PC_Monitor_Host` 值。

---

## 14. 异常处理与降级策略

| 场景 | 处理 |
|------|------|
| 单采集器异常 | 捕获日志，字段 N/A，不影响其他采集器 |
| GPU 进程显存为 None | 判空跳过，不影响整体 GPU 采集（§8.3.4） |
| 单 Agent 断开 | 仅移除该连接，不影响其他 Agent；该 Agent 标记离线并独立重连 |
| 端口占用 | 启动检测，提示并退出 |
| 温度/帧率不可用 | 静默 N/A，不弹窗 |
| 损坏 JSON 帧 | 丢弃该帧，等下一帧 |
| 鉴权失败 | 关闭 WS 连接（close 1008），Host 标记"鉴权失败" |
| 已有实例运行 | 提示并退出 |
| UDP 广播/监听失败 | 记录日志，Host 可手动连接 |

### 14.1 阈值变色（三级）

| 指标 | 正常（绿） | 警告（橙） | 危险（红） |
|------|-----------|-----------|-----------|
| CPU/GPU 使用率 | <80% | 80~95% | >95% |
| 内存使用率 | <80% | 80~90% | >90% |
| CPU/GPU 温度 | <80°C | 80~85°C | >85°C |
| GPU 热点 | <95°C | 95~105°C | >105°C |
| 磁盘使用率 | <85% | 85~95% | >95% |
| 网络评分 | ≥90 | 60~79 | <60 |
| RTT | <5ms | 5~20ms | >20ms |

颜色（QSS）：背景 `#1e1e1e`，文字 `#d4d4d4`，绿 `#4ec9b0`，橙 `#d7ba7d`，红 `#f44747`，N/A 灰 `#808080`。

---

## 15. 性能兜底机制

### 15.1 目标与降级

监控程序自身 CPU 占用应 **< 2%**。超限时自动降级：

```python
class SelfMonitor:
    """自监控：检测本程序 CPU 占用，超限自动降级（Agent / Host 本机共用）"""
    def __init__(self, aggregator, collectors, interval=10.0):
        self.aggregator = aggregator
        self.collectors = collectors
        self.proc = psutil.Process()
        self._prewarmed = False   # cpu_percent 是否已预热
        self._streak = 0          # 连续超阈值次数

    def check(self):
        try:
            cpu = self.proc.cpu_percent(interval=1.0)
        except Exception:
            return
        # 预热：首次调用返回自启动以来平均值（可能虚高），丢弃不评估
        if not self._prewarmed:
            self._prewarmed = True
            return
        if cpu > 5.0:
            self._streak += 1
            if self._streak >= 2:   # 连续 2 次超阈值才降级（防单次抖动）
                self.aggregator.interval = 2.0          # 1s → 2s
                if "fps" in self.collectors:
                    self.collectors["fps"].stop()       # 关闭帧率
                self._streak = 0
        elif cpu < 3.0:
            self._streak = 0
            if self.aggregator.interval > 1.0:
                self.aggregator.interval = 1.0          # 恢复频率（帧率不自动恢复）
```

- **阈值**：CPU > 5% 触发降级（采集频率 1s→2s + 关闭帧率）；CPU < 3% 恢复采集频率（帧率不自动恢复，避免抖动）。
- **健壮性**：`cpu_percent` 首次调用返回自进程启动以来的平均值（可能虚高，如初始化期间 62%），故**首次采样仅作预热丢弃**；且需**连续 2 次超阈值**才降级，避免单次瞬时抖动误关帧率。
- **自监控频率**：每 10 秒检查一次。

---

## 16. 依赖清单与部署

### 16.1 依赖清单（v5.0 · 双端分离，拆分安装）

> **依赖归属**：`common/` 为共用代码（协议/采集器/工具），其依赖（psutil、wmi、pywin32 等）Agent 与 Host 均需要。依赖已**拆分为三份文件**，按角色安装（见 §16.5 打包约束）。

**安装方式**：

```bash
# 一键安装全部（开发/调试）
pip install -r requirements-agent.txt -r requirements-host.txt

# 仅 Agent（被监控机）：共用 + Agent 依赖
pip install -r requirements-agent.txt

# 仅 Host（监控机）：共用 + Host 依赖
pip install -r requirements-host.txt
```

**`requirements-common.txt`**（共用，两端都要）：

```
psutil>=5.9.0
py-cpuinfo>=9.0.0
nvidia-ml-py>=11.5.0   # GPU（import pynvml；NVML 随 NVIDIA 驱动自带，无需 CUDA）
wmi>=1.5.1
pywin32>=305
numpy>=1.24.0           # 帧差分计算（dxcam 依赖）
dxcam>=0.0.5            # DXGI 截帧降级（仅 Windows）
netifaces>=0.11         # 多网卡 IP（无 MSVC 时自动降级 UDP 兜底）
zeroconf>=0.132.0       # mDNS 自动发现（未安装时降级仅 UDP 广播）
pyadl>=0.1              # AMD GPU（可选，实验性）
```

**`requirements-agent.txt`**（Agent 必需）：

```
-r requirements-common.txt
websockets>=12.0        # Agent WebSocket 服务端
aiohttp>=3.9.0          # Agent HTTP/REST 服务端（与 WS 共用端口）
```

**`requirements-host.txt`**（Host 必需）：

```
-r requirements-common.txt
PyQt5>=5.15.0           # Host GUI（原生桌面，见 §6.2）
websocket-client>=1.7   # Host WS 客户端
requests>=2.31.0        # Host REST API 客户端
```

> **打包裁剪原则（依赖粒度）**：Agent 发布包**不包含** PyQt5/websocket-client/requests（后台无 GUI）；Host 发布包**不包含** aiohttp/websockets（仅作客户端，用更轻的 `websocket-client` + `requests`）。共用依赖（psutil 等）两端各自打包进各自的产物，互不共用安装目录。双端分离打包的强制规定见 §16.5。

**依赖说明**：

| 包 | 归属 | 用途 | 平台 | 备注 |
|----|------|------|------|------|
| `websockets` | Agent | WebSocket 服务端 | 全平台 | 也可用 aiohttp 内置 WS 实现 |
| `aiohttp` | Agent | HTTP/REST 服务端 | 全平台 | 提供 `/api/*` 与可选的 WS |
| `PyQt5` | Host | 原生 GUI | 全平台 | 主窗口/详情面板/概览/告警托盘 |
| `websocket-client` | Host | WS 客户端 | 全平台 | 订阅 Agent 推送 |
| `requests` | Host | REST 客户端 | 全平台 | 调用 `/api/*`（健康/配置/扫描） |
| `nvidia-ml-py` | 共用 | NVIDIA GPU（pynvml） | 全平台 | 需驱动 ≥ 350；**≥13 版 `usedGpuMemory` 可能返回 None，需判空** |
| `dxcam` | 共用 | DXGI 帧率降级 | **仅 Windows** | 全屏独占下失败 |
| `netifaces` | 共用 | 多网卡 IP | 全平台 | 无 MSVC 时自动降级 socket UDP |
| `zeroconf` | 共用 | mDNS 零配置发现 | 全平台 | 未安装/不可用时自动降级 |
| `pyadl` | 共用 | AMD GPU | 全平台 | 实验性，仅使用率/温度/频率 |

> **pyadl 可用性（明确）**：`pyadl` 多年未更新，基于旧版 ADL/ADLX SDK，**在较新 AMD 驱动上可能完全失效**。采集器需捕获初始化失败，整体降级为 N/A；依赖置为可选。

### 16.2 防火墙放行

PowerShell（管理员）：

```powershell
New-NetFirewallRule -DisplayName "PC_Monitor_HTTP" -Direction Inbound -Protocol TCP -LocalPort 12345 -Action Allow -Profile Private
New-NetFirewallRule -DisplayName "PC_Monitor_UDP"  -Direction Inbound -Protocol UDP -LocalPort 12346 -Action Allow -Profile Private
```

### 16.3 部署步骤

1. 装 Python 3.10+。
2. **按角色装依赖**：被监控机 `pip install -r requirements-agent.txt`；监控机 `pip install -r requirements-host.txt`（或开发机一键全装，见 §16.1）。
3. （可选）下载 PresentMon.exe → `tools/`。
4. （可选）安装 LibreHardwareMonitor（温度/功耗）。
5. 防火墙放行 12345/12346。
6. **副机端 Agent** 以管理员运行 `agent/`（`python -m agent`）（温度/帧率需提权），生产环境用 `pythonw.exe` 或注册服务；可选 `python -m agent --gui` 带本机仪表盘。
7. **主机端 Host** 运行 `host/`（`python -m host`）（集中监控大屏，无需提权）。
8. （可选）`python -m agent --install-startup` / `python -m host --install-startup` 装开机自启。

### 16.4 权限说明

| 功能 | 需管理员 |
|------|---------|
| CPU/GPU 使用率、内存、磁盘空间、网络速率 | 否 |
| 温度/功耗（LibreHardwareMonitor） | **是** |
| PresentMon ETW 帧率 | **是** |
| 系统命令 `ping` 解析 | 否 |
| Agent 开机自启（schtasks /RL HIGHEST） | **是**（安装时） |
| Host 开机自启（注册表 Run） | 否 |

### 16.5 打包与分发约束（强制）

> **核心原则**：Agent（服务端）和 Host（客户端）是**两个独立的软件产品**，必须**独立构建、独立打包、独立分发、独立部署**。严禁将两者合并为一个单一安装包或单一可执行文件。本节为**强制规定**，打包/发布必须遵守。

#### 16.5.1 强制规定

| 维度 | 副机端 Agent | 主机端 Host |
|------|--------------|-------------|
| **构建系统** | PyInstaller 独立 spec 配置（`agent.spec`） | PyInstaller 独立 spec（`host.spec`） |
| **输出产物** | 独立可执行文件 / 安装包（如 `PC-Monitor-Agent-Setup.exe`） | 独立可执行文件 / 安装包（如 `PC-Monitor-Host-Setup.exe`） |
| **安装目录** | 默认 `C:\Program Files\PC-Monitor\Agent\` | 默认 `C:\Program Files\PC-Monitor\Host\`（**不与 Agent 混装**） |
| **运行方式** | 后台服务 / 系统托盘，无主界面（可选原生 PyQt5 本机仪表盘） | 前台桌面应用程序（PyQt5），独立进程 |
| **配置文件** | 独立 `agent_config.json`（存在 Agent 目录） | 独立 `host_config.json`（存在 Host 目录） |
| **日志目录** | `logs/agent.log` | `logs/host.log` |

#### 16.5.2 严禁行为（红线）

- ❌ **禁止** 将 Agent 和 Host 打包到同一个 `.exe` 或同一个安装包中。
- ❌ **禁止** 共用同一份 `config.json` 或同一套资源文件。
- ❌ **禁止** 通过命令行参数在同一个 Python 进程中同时启动 Agent 和 Host（`python -m agent` 与 `python -m host` **必须为两个独立进程入口**）。
- ❌ **禁止** 在 Host 安装包中内嵌 Agent 可执行文件，或反过来。

#### 16.5.3 产出物与发布规范

**独立发布渠道**

| 发布包 | 命名规范 |
|--------|----------|
| Agent | `PC-Monitor-Agent-v5.0-win-x64.exe` |
| Host | `PC-Monitor-Host-v5.0-win-x64.exe` |

- 两者**分别提供下载链接**，用户按需安装：被监控机装 **Agent**，监控机装 **Host**。

**安装互不干扰**

- 安装路径允许用户自定义，但**默认路径必须分离**（Agent → `...\Agent\`，Host → `...\Host\`）。
- 注册表项、计划任务、快捷方式均需带**角色后缀**（如 `PC_Monitor_Agent`、`PC_Monitor_Host`），避免互相覆盖。
- **单实例互斥独立**：
  - Agent 单实例互斥体名：`Global\PC_Monitor_Agent`
  - Host 单实例互斥体名：`Global\PC_Monitor_Host`
  - 两者互不冲突，**允许在同一台电脑上同时运行**（此时该电脑既是被监控机也是监控机）。

#### 16.5.4 开发期与打包期检查清单

- [ ] 依赖**明确区分** Agent 必需与 Host 必需：`requirements-common.txt`（共用）/ `requirements-agent.txt` / `requirements-host.txt`（§16.1）。
- [ ] 打包脚本（如 `build_agent.py` 与 `build_host.py`）**分离**，各自独立触发。
- [ ] CI/CD 流水线**分别产出两个制品**，发布到不同目录/标签。
- [ ] 文档明确说明"**双端分离，按需安装**"，并列明各自系统要求（Agent 建议管理员、Host 普通用户即可）。

---

## 17. 目录结构规划

```
远程监控电脑状态/
├── docs/                         # 📁 文档归档
├── tests/                        # 📁 测试脚本
│   ├── test_p0.py                # 自检（帧协议/鉴权/链路/采集器/评分/连接码等）
│   ├── test_connect.py           # 双端连接端到端测试（v5.0 弃用，见 test_api）
│   ├── test_p4.py                # P4 集成测试（v5.0 弃用，见 test_api）
│   └── test_api.py               # （v5.0）REST + WebSocket 端到端
├── requirements.txt               # 依赖清单（含拆分安装指南，见 §16.1）
├── requirements-common.txt        # 共用依赖（Agent + Host）
├── requirements-agent.txt         # Agent 额外依赖（websockets/aiohttp）
├── requirements-host.txt          # Host 额外依赖（PyQt5/websocket-client/requests）
├── build_agent.py                 # Agent 独立打包脚本（§16.5）
├── build_host.py                  # Host 独立打包脚本（§16.5）
├── agent.spec                     # PyInstaller Agent 独立 spec
├── host.spec                      # PyInstaller Host 独立 spec
├── start_agent.bat               # Agent 启动批处理（菜单：启动/装自启/卸自启）
├── start_host.bat                # Host 启动批处理（菜单：启动/装自启/卸自启）
├── common/                       # 公共模块
│   ├── __init__.py
│   ├── protocol.py              # WS 消息类型 / REST 封装（替代 v4.0 send_frame）
│   ├── utils.py                 # 单位换算、IP 获取、网关 ping、端口检测、连接串解析等
│   ├── logger.py                # RotatingFileHandler 日志
│   ├── single_instance.py       # 单实例检测（命名互斥体）
│   ├── startup.py               # 开机自启安装/卸载
│   ├── quality.py               # 网络质量评分器（滑动平均）
│   ├── lhm.py                   # LibreHardwareMonitor 温度读取
│   ├── connect_code.py          # 连接码生成/解析、.pcm 导入导出
│   ├── connect_dialog.py        # 连接码/剪贴板/首屏引导对话框
│   └── theme.py                 # 深色主题/变色规则
├── agent/                        # 副机端模块（服务端）
│   ├── __init__.py / __main__.py / main.py   # python -m agent 入口
│   ├── config.py                # agent_config.json 读写
│   ├── http_server.py           # REST API（/api/health|nodes|scan|config）
│   ├── websocket_server.py      # WS 服务端（/ws 多订阅推送 + PING 处理）
│   ├── discovery.py             # UDP/mDNS 广播与注册（agent_heartbeat，自实现）
│   ├── aggregator.py            # 数据聚合器（最新帧缓存）
│   ├── self_monitor.py          # 性能兜底（复用 common.self_monitor）
│   └── gui/
│       ├── __init__.py
│       └── main_window.py       # 本机仪表盘（AgentDashboardWindow，--gui 模式）
├── host/                        # 主机端模块（原生 PyQt5 前端）
│   ├── __init__.py / __main__.py / main.py   # python -m host 入口
│   ├── config.py                # host_config.json 读写
│   ├── connection.py            # AgentConnection（WebSocket 客户端，v5.0）
│   ├── discovery.py             # UDP/mDNS 监听与发现
│   ├── local_node.py            # 本机节点（本地采集器，可选）
│   ├── self_monitor.py          # 性能兜底（转发 common.self_monitor）
│   ├── alerts.py                # 红线告警引擎（第四篇）
│   └── gui/
│       ├── main_window.py       # 主窗口（自适应布局 + 添加入口）
│       ├── node_list.py         # 左侧节点列表（右键菜单）
│       ├── detail_panel.py      # 右侧详情面板
│       ├── overview_grid.py     # 概览卡片网格
│       └── discovery_dialog.py  # 自动发现弹窗（多选 + 一键添加）
├── i18n/                        # 📁 多语言资源
│   ├── zh_CN.json
│   └── en.json
├── tools/
│   └── PresentMon.exe           # 帧率工具（需手动下载）
└── logs/                        # 运行日志（自动创建）
    ├── agent.log
    └── host.log
```

> **Host GUI 说明（§6.2）**：Host 端采用**原生 PyQt5**，打包为独立 exe。`host/gui/` 为 PyQt5 实现，网络层（未来 WS 客户端）与 GUI 解耦，仅通过信号/回调供界面消费。若未来确需 Web 化，可整体替换 `host/gui/` 为 Electron 渲染层，不影响网络层与告警/采集逻辑。

> **采集器复用**：`agent/collectors/` 与 Host 本机节点共用同一套采集器代码（本机节点直接 import `agent.collectors`），保证本机与远程节点数据同构。
>
> **入口方式**：主入口统一 `python -m agent` / `python -m host`（bat 菜单调用）。
>
> **已清理**：v4.0 的 `node/`（采集节点）、`client/`（副机端）目录已在 v5.0 迁移中删除——采集器迁至 `common/collectors/`，采集+推送能力并入 `agent/`，副机端本机仪表盘并入 `agent/gui/`。

## 18. 启动脚本与批处理

### 18.1 start_agent.bat（菜单式）

```bat
@echo off
chcp 65001 >nul
title 副机端 Agent（服务端 · 后台）菜单
:menu
cls
echo ============================================
echo        副机端 Agent（采集 + WS/REST 服务）
echo        （普通权限可运行基本采集；温度/帧率建议管理员）
echo ============================================
echo  1. 启动 Agent 后台服务（无界面，建议管理员）
echo  2. 启动 Agent + 本机仪表盘（--gui，PyQt5）
echo  3. 安装开机自启动（需管理员，schtasks /RL HIGHEST）
echo  4. 卸载开机自启动
echo  0. 退出
echo ============================================
set /p choice=请选择:

if "%choice%"=="1" (
    python -m agent
    goto end
)
if "%choice%"=="2" (
    python -m agent --gui
    goto end
)
if "%choice%"=="3" (
    python -m agent --install-startup
    goto end
)
if "%choice%"=="4" (
    python -m agent --remove-startup
    goto end
)
if "%choice%"=="0" exit
echo 无效选择，请重新输入。
:end
pause
goto menu
```

### 18.2 start_host.bat（菜单式）

```bat
@echo off
chcp 65001 >nul
:menu
cls
echo ============ 主机端 Host（集中监控大屏 · 纯前端） ============
echo （无需管理员权限；仅当需要查看本机温度/帧率时才建议以管理员运行）
echo 1. 启动 Host
echo 2. 安装开机自启动（注册表 Run，无需管理员）
echo 3. 卸载开机自启动
echo 0. 退出
set /p choice=请选择:
if "%choice%"=="1" python -m host
if "%choice%"=="2" python -m host --install-startup
if "%choice%"=="3" python -m host --remove-startup
if "%choice%"=="0" exit
pause
goto menu
```

> Agent .bat 提示"需管理员"：可检测当前是否管理员，非则提示右键以管理员运行。安装 schtasks 必须管理员。

---

## 19. UI 交互细节与边界场景补充

> 本章针对 GUI 交互、多节点语义、性能兜底、网络选择等边界场景给出明确规范。多数沿用 v4.0，仅将"节点"替换为"Agent"、网络通道替换为 WebSocket/REST。

### 19.1 节点列表项显示规范

**列表项布局**（Host 左侧列表 / 概览模式卡片头部通用）：

```
┌──────────────────────────────────────────────┐
│ 游戏主机                          [RTT 0.45ms] [98 优秀] │
│ 192.168.1.100  ● 已连接                             │
└──────────────────────────────────────────────┘
```

- **左侧**：别名（大号粗体）+ 换行 IP 地址 + 状态指示点（● 绿 已连接 / ● 橙 重连中 / ● 红 离线/鉴权失败）。
- **右侧**：两个小标签（`QLabel` 圆角背景）：
  - `RTT 0.45ms`——当前 RTT，颜色随阈值变色（<5ms 绿 / 5~20ms 橙 / >20ms 红）。**本机节点固定显示 `RTT 0.00ms`（绿）**。
  - `98 优秀`——网络评分 + 等级，评分数字随阈值变色。**本机节点评分统一显示为 `—`（长横杠，灰色）**（本机数据不经过网络，评分无意义）。
- **本机节点**：默认关闭（§6.5），仅在用户手动启用后出现在列表顶部并显示 `[本机]` 标识。
- **选中高亮**：选中某节点，该列表项背景高亮（`#2d2d30` + 左侧 2px 蓝色竖条 `#007acc`），右侧详情面板切换为该节点数据。选中状态在数据更新、断线重连过程中持续保持。
- **实时更新**：列表项摘要（RTT/评分/状态）随每秒数据帧实时变化。
- **右键菜单**：移除节点、编辑别名、手动重连（本机节点不可移除/重连）。

### 19.2 概览卡片排布与数量限制（Host 端）

**单张卡片布局**（3 列 × 2 行网格，共 6 项关键指标）：

```
┌────────────────────────────────────────────┐
│ 游戏主机              192.168.1.100          │
│ ● 已连接   RTT 0.45ms   98 优秀              │
├──────────────┬──────────────┬──────────────┤
│ CPU  45%     │ GPU  62%     │ 内存 50%      │
│ (绿)         │ (绿)         │ (绿)         │
├──────────────┼──────────────┼──────────────┤
│ CPU 65°C     │ GPU 68°C     │ FPS 142      │
│ (绿)         │ (绿)         │ (绿)         │
└──────────────┴──────────────┴──────────────┘
```

- **卡片网格**：`QGridLayout`，每行最多 4 张（`max_cards_per_row` 可配），间距 12px，自适应等宽。
- **关键指标**（固定 6 项）：CPU 使用率、GPU 使用率、内存使用率、CPU 温度、GPU 温度、FPS，随阈值变色。
- **点击卡片**：切换到该节点详情视图。
- **数量限制**：`max_overview_cards`（默认 16），超过启用横向滚动，右上角显示"共 N 台，显示前 M 台"。本机节点卡片也参与概览。

### 19.3 阈值变色实现

采用 `QLabel.setStyleSheet` 动态切换文字颜色：

```python
# common/theme.py 中定义颜色与阈值（Agent 本机仪表盘 / Host 共用）
COLOR_NORMAL = "#4ec9b0"   # 绿
COLOR_WARN   = "#d7ba7d"   # 橙
COLOR_DANGER = "#f44747"   # 红
COLOR_NA     = "#808080"   # 灰（N/A）

def usage_color(percent):
    if percent == "N/A" or percent is None: return COLOR_NA
    if percent > 95: return COLOR_DANGER
    if percent > 80: return COLOR_WARN
    return COLOR_NORMAL

def temp_color(temp_c):
    if temp_c == "N/A" or temp_c is None: return COLOR_NA
    if temp_c > 85: return COLOR_DANGER
    if temp_c > 80: return COLOR_WARN
    return COLOR_NORMAL

def apply_color(label, color):
    label.setStyleSheet(f"color: {color}; font-family: Consolas, 'Microsoft YaHei';")
```

> 全部变色逻辑集中在 `common/theme.py`，阈值参数化、N/A 统一灰色，不参与变色。

### 19.4 `connected_clients` 语义与去重

**问题**：v4.0 中 `client_count()` 返回 TCP 连接数，但同一显示端多线程连接会重复计数。

**方案（v5.0）**：WebSocket 每个订阅连接天然是一个独立连接；`connected_clients` 直接统计**当前 WS 订阅者数量**（按连接去重，同一 Host 的多标签页/多窗口按连接计）。Agent 在聚合帧中填充 `connected_clients = ws_server.subscriber_count()`，表示"几台 Host/浏览器正在订阅本 Agent"。

### 19.5 RTT 在多 Host 场景的语义

- **RTT 由各 Host 测量，不由 Agent 测量**。每台 Host 独立经 WebSocket **PING 帧**测量，Agent 端由底层自动回 **PONG**，Host 本地计算 `RTT = perf_counter() - ts`（§4.2）。RTT 本质是**每台 Host 对各 Agent 的独立测量值**。
- **Agent 端 `net_quality.latency_to_client_ms` 字段**：多 Host 场景下意义有限，**填 `null`**，RTT 完全由 Host 本地测量并显示。
- **Host 端**：`rtt_updated` 信号带 `node_id`，GUI 按 node_id 显示该节点与本端之间的 RTT。本机节点 RTT 固定 0.00ms。

### 19.6 PresentMon 分发与许可

- **项目地址**：https://github.com/GameTechDev/PresentMon
- **许可证**：MIT License，允许随程序分发与商用，需保留版权声明。
- **分发要求**：`PresentMon.exe` 放入 `tools/`；`tools/LICENSE-PresentMon.txt` 保留许可证；README 注明来源。
- **下载方式**：检测 `tools/PresentMon.exe` 不存在时日志提示用户从 GitHub Releases 下载，不自动联网下载。
- **替代方案**：仅启用 DXGI 截帧降级（`"collectors": {"fps": "dxgi"}`）。

### 19.7 自动发现与手动添加的混合场景

- **手动添加 Agent**：写入 `host_config.json.hosts`，状态由 WS 连接结果决定，**与 UDP 心跳无关**：
  - 连接成功 → "已连接"
  - 连接失败/断开 → "离线"，**不从列表消失**，自动触发指数退避重连（§4.6）
  - 重连中 → "重连中(Ns)"
  - 鉴权失败 → "鉴权失败"（停止重连，需检查 token）
- **自动发现 Agent**：来自 UDP 心跳/mDNS，仅在"自动发现弹窗"中临时显示，10 秒无心跳移除。用户批量添加后转为手动节点，此后即使心跳消失也保留。
- **去重**：手动添加时，若 IP+端口已存在，提示"已添加过"。
- **状态机**（每台手动 Agent）：
  ```
  离线 ──(重连协程)──> 重连中 ──(成功)──> 已连接
    ▲                    │
    └────(失败/超时)─────┘
                          └──(鉴权失败)──> 鉴权失败（停止重连，需用户检查 token）
                          └──(断开)──> 离线（继续重连）
  ```

### 19.8 GUI 刷新频率（可独立调节，预留）

- 在 `host_config.json` 增加 **`gui_refresh_interval`**（秒，默认 `1.0`）。
- GUI 主线程用 `QTimer` 驱动界面刷新，将数据帧缓存到 `dict[node_id] = latest_frame`，每 `gui_refresh_interval` 秒从缓存取最新帧重绘。
- **帧率/评分不受影响**：接收线程与采集线程仍按各自频率运行，仅"界面重绘"节拍可调。

### 19.9 FPS 降级日志的"源头"覆盖

- 该降级提示（"PresentMon.exe 未找到，已自动降级为 DXGI 截帧模式……"）由**帧率采集器本身**（`agent/collectors/fps_collector.py`）统一打印，日志写入当前运行端的日志文件（`logs/agent.log` / `logs/host.log`）。
- 采集器实例被 Agent 与 Host 本机节点复用时，提示自然随各端日志出现。

## 20. REST API 与 WebSocket 参考

> 本章为 §4 协议的完整参考，供前后端联调直接对照。所有 REST 请求需携带 token：`Authorization: Bearer <token>` 或 `?token=<token>`。

### 20.1 REST 接口

#### `GET /api/health` — 健康检查

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

#### `GET /api/nodes` — 获取本机信息与节点管理结果

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

#### `POST /api/scan` — 触发自动发现扫描

请求体（可选）：

```json
{"timeout": 3}
```

响应：

```json
{
  "found": [
    {"hostname":"GAME-PC-2","ip":"192.168.1.124","port":12345,
     "token_hash":"a1b2c3d4"}
  ]
}
```

> `token_hash` 为 token 的 SHA-256 前 8 位，用于候选匹配（连接码/发现结果校验），不泄露完整 token。

#### `GET /api/config` — 读取配置

```json
{
  "http_port": 12345,
  "udp_port": 12346,
  "collectors": {"fps": "presentmon", "gpu": true, "temperature": true},
  "log_level": "INFO",
  "gpu_index": 0
}
```

> **不返回 token**（敏感字段排除）。
>
> **token 修改方式（明确）**：token **不提供任何修改/重置 API**，仅通过本地配置文件 `agent_config.json` 手工修改（需重启 Agent 生效），防止经网络越权改凭据。

#### `POST /api/config` — 更新配置

```json
{"alias": "新别名", "log_level": "DEBUG"}
```

```json
{"ok": true}
```

> 支持更新节点别名、日志级别、采集器开关等；token 不可经此接口修改（防越权）。

### 20.2 mDNS 自动发现

**依赖**：`zeroconf>=0.132.0`。未安装或启动失败时自动降级，仅保留 UDP 广播。

**服务类型**：`_pcmonitor._tcp.local.`，每台 Agent 以 `{hostname}._pcmonitor._tcp.local.` 注册。

**Agent 端注册**：

```python
from zeroconf import ServiceInfo, Zeroconf

def register_mdns(ip, port, hostname, token):
    service_info = ServiceInfo(
        "_pcmonitor._tcp.local.",
        f"{hostname}._pcmonitor._tcp.local.",
        addresses=[socket.inet_aton(ip)],
        port=port,
        properties={
            "hostname": hostname,
            "token_hash": hashlib.sha256(token.encode()).hexdigest()[:8],
        },
    )
    zc = Zeroconf()
    zc.register_service(service_info)
    return zc  # 保持引用防止服务下线
```

> token 仅广播 **SHA-256 前 8 位摘要**，不泄露完整 token。

**Host 端发现**：

```python
from zeroconf import ServiceListener, Zeroconf

class MonitorListener(ServiceListener):
    def add_service(self, zc, type_, name):
        info = zc.get_service_info(type_, name)
        if info:
            ip = socket.inet_ntoa(info.addresses[0])
            port = info.port
            hostname = info.properties.get(b"hostname", b"").decode()
            # 自动添加到节点列表，状态为"待连接"

    def remove_service(self, zc, type_, name):
        # 服务下线 → Agent 标记离线（不从列表移除，按 §19.7 规则）

    def update_service(self, zc, type_, name):
        # IP 变化时实时更新节点地址
```

- **自动填充**：启动后自动创建 `Zeroconf()` + 注册监听，在线 Agent 在几秒内自动进入列表（状态"待连接"），点击"接入"即可。
- **mDNS 与 UDP 广播并行运行**，互为备份：mDNS 优先同一子网；UDP 广播作为兼容层。
- **去重**：mDNS 发现与 UDP 扫描按 `ip:port` 去重。

### 20.3 UDP 自动发现

Agent 每 2 秒广播心跳（UDP `255.255.255.255:12346`，或组播 `239.0.0.1`）：

```json
{"type":"agent_heartbeat","hostname":"GAME-PC","ip":"192.168.1.100",
 "http_port":12345,"token":"abc123","ts":1722892800.0}
```

Host 端监听 UDP 12346，维护 `dict[ip] = {hostname, http_port, token, last_seen}`，**超过 10 秒无心跳**标记离线并移除。

### 20.4 连接码接入

**连接码格式**：6 位纯数字（如 `482913`），由 Agent 启动时生成，编码 `ip:port:token` 的 SHA-256 摘要取数字部分前 6 位：

```python
import hashlib

def make_connect_code(ip, port, token) -> str:
    raw = f"{ip}:{port}:{token}"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    digits = "".join(c for c in digest if c.isdigit())
    return (digits or "000000")[:6]

def resolve_connect_code(code: str, candidates: dict) -> dict | None:
    code = code.strip()
    for ip, info in candidates.items():
        if make_connect_code(ip, info["port"], info["token"]) == code:
            return {"ip": ip, **info}
    return None
```

> **解析方式**：连接码不含明文地址，需结合本地 mDNS/UDP 发现的候选 Agent 做摘要匹配（同网段有效）；跨网段场景提示用户改用 .pcm 配置导入。

### 20.5 .pcm 配置文件

**格式**：JSON 文本（UTF-8），token 做混淆（Base64 + XOR 简单加密，防明文泄露）：

```json
{
  "format": "pcmonitor-config",
  "version": 1,
  "exported_at": "2026-08-10T20:00:00",
  "agents": [
    {"alias": "游戏主机", "ip": "192.168.1.100", "port": 12345,
     "token_enc": "b2M6..."}
  ]
}
```

**导入导出流程**：
- **导出**：`common/connect_code.py` 中 `export_config(agents, path)` → 序列化 + token 混淆 → 写入 `.pcm`。
- **导入**：`import_config(path)` → 校验 `format`/`version` → 解密 token → 逐 Agent `upsert_host`。
- **GUI**：Host 端"导出配置"按钮与"导入配置"按钮（或窗口拖放 `.pcm` 文件）。

### 20.6 剪贴板连接串

**格式**：`pcmonitor://<ip>:<port>?token=<token>&alias=<别名>`（URL 编码别名）。

```python
from urllib.parse import urlparse, parse_qs, quote

def parse_connect_uri(text: str) -> dict | None:
    """解析 pcmonitor:// 连接串，失败返回 None"""
    try:
        u = urlparse(text.strip())
        if u.scheme != "pcmonitor":
            return None
        q = parse_qs(u.query)
        return {
            "ip": u.hostname,
            "port": u.port or 12345,
            "token": (q.get("token") or [""])[0],
            "alias": (q.get("alias") or [""])[0],
        }
    except Exception:
        return None
```

### 20.7 首屏引导

- Host 端**首次运行**（配置文件不存在或 `onboarded` 标记缺失）时，弹出引导对话框：
  1. 提示"正在扫描局域网内的 Agent..."，后台启动 mDNS + UDP 扫描，展示进度。
  2. 扫描完成展示发现的 Agent 列表，按 **IP 段匹配度** 降序（与本机同网段优先）。
  3. 提供"一键接入全部"按钮批量接入；也可关闭引导手动添加。
- 引导完成后写入 `onboarded: true`，下次启动不再弹出。

---

## 21. 功能实现的理论效果

> 本章描述 v5.0 前后端分离架构下，各功能模块**实现后应达到的运行效果与用户可感知行为**，作为开发联调与验收的目标参照。与 §24 验收清单配合使用。

### 21.1 整体运行效果

- **被监控电脑**运行一个副机端 Agent（后台服务）：开机自动启动（`--install-startup` 装 schtasks 计划任务，管理员权限），静默采集本机硬件并每 1 秒推送；不弹任何窗口（`pythonw.exe` / 打包 exe 后台运行）。
- **监控电脑**运行一个主机端 Host（PyQt5 桌面应用）：打开后自动出现在已配置 Agent 列表中的各节点，**1 秒内**刷新出各节点实时数据；集中大屏展示全部节点的 CPU/GPU/内存/温度/帧率/评分等指标，阈值三级变色。
- 同一 Agent 可被**多台 Host 同时连接订阅**（WebSocket 多客户端广播）；Agent 之间互不通信。
- 若在被监控电脑上执行 `python -m agent --gui`，则弹出一个**本机仪表盘**窗口——本地数据直供显示（不经网络），同时后台服务照常运行；关闭窗口即停服务。

### 21.2 副机端 Agent 各功能效果

| 功能 | 实现后的理论效果 |
|------|------------------|
| **后台采集** | 每 1 秒采集 CPU/GPU/内存/磁盘/网络/帧率/进程/系统/网络质量，异常采集器降级为 N/A 不影响其他；监控程序自身 CPU 占用 < 2%，超限自动降级（采集频率 1s→2s + 关帧率） |
| **WebSocket 推送** | 已订阅的 Host 每 1 秒收到一帧 `monitor_data`（JSON），首帧为 `auth_result`；鉴权失败立即关闭连接（close 1008 / 401） |
| **REST API** | `/api/health` 返回服务状态；`/api/nodes` 返回本机信息；`/api/config` 可读配置（不含 token）且 token 不可经 API 修改 |
| **本机仪表盘（`--gui`）** | 弹出 PyQt5 窗口：分区显示本机全部指标（阈值变色），顶部连接信息区（IP/端口/Token/连接串一键复制），底部显示 HTTP/WS 端口与订阅者数；关闭窗口停止后台服务 |
| **自动发现** | 每 2 秒 UDP 广播 `agent_heartbeat`（含 http_port/token），并行注册 mDNS `_pcmonitor._tcp.local.`；Host 打开后几秒内自动发现并填入节点列表 |
| **单实例 / 端口检测** | 二次启动提示"已有实例运行"并退出；端口被占用时报错退出 |

### 21.3 主机端 Host 各功能效果

| 功能 | 实现后的理论效果 |
|------|------------------|
| **节点列表（左侧）** | 显示所有已配置/已发现 Agent：别名、IP、状态（●在线/●重连中/●离线/鉴权失败）、RTT、评分摘要；离线节点保留并自动重连 |
| **详情面板（右侧）** | 点击节点显示该节点全部指标分区（CPU/内存/GPU/磁盘/网络/网络质量/帧率/进程），数值每秒刷新，阈值三级变色（绿/橙/红），N/A 灰色 |
| **概览视图** | 网格卡片展示各节点关键指标（CPU/GPU/内存/温度/FPS/评分），适合大屏；卡片超上限横向滚动 |
| **红线告警** | 自定义红线阈值，越线时状态栏红色提示 + 日志 WARNING + 系统托盘气泡（去重：状态变化弹一次） |
| **RTT / 丢包** | 每台 Host 独立经 WebSocket PING + loss_pong 精确测量各节点 RTT（<1ms 精度）与丢包率，注入评分 |
| **节点管理** | 六种接入方式（mDNS 自动发现 / UDP 扫描 / 连接码 / .pcm 导入导出 / 剪贴板连接串 / 手动添加），配置持久化到 `host_config.json`，重启自动重连 |

### 21.4 通信链路效果

- **实时性**：WebSocket 每秒推送，Host 端延迟 < 1 秒（局域网）。
- **鉴权**：连接 Agent 时 URL 携带 `?token=`，握手阶段校验；错误 token 立即被拒（401/close 1008），日志记录。
- **断线重连**：任一 Agent 断开，Host 独立指数退避重连（1s→60s 封顶），连上后数据流自动恢复；多 Agent 同时断线互不影响。
- **数据完整性**：`monitor_data` 帧结构固定（§7 Schema），字段缺失/异常统一 `N/A`，GUI 显示 N/A 并跳过变色。

### 21.5 运维与部署效果

- **双端独立打包**：Agent 与 Host 各自产出独立 exe/安装包（`PC-Monitor-Agent-v5.0-win-x64.exe` / `PC-Monitor-Host-v5.0-win-x64.exe`），独立安装目录、独立配置、独立日志，互不混装（§16.5 红线）。
- **开机自启**：Agent 用 schtasks（需管理员，`/RL HIGHEST` 提权）；Host 用注册表 Run（无需管理员）。
- **日志轮转**：`logs/agent.log` / `logs/host.log`，单文件 10MB、保留 5 份，UTF-8。
- **防火墙**：放行 TCP 12345（HTTP/WS）与 UDP 12346（自动发现，可选）。

---

## 22. 扩展方向（非必须，锦上添花）

| 优化点 | 说明 | 建议方案 |
|--------|------|----------|
| **历史数据趋势图** | 当前为实时监控，无历史曲线 | 增加"最近 1 小时 CPU/GPU 趋势图"，用 **pyqtgraph** 或前端图表库（ECharts/Chart.js），对游戏性能分析很有价值 |
| **告警规则自定义** | 当前阈值固定（§14.1） | 第四篇红线告警已支持自定义；可进一步支持运行时热编辑 |
| **Agent Windows 服务化** | 当前用 schtasks + pythonw.exe 后台运行 | 打包为 **Windows 服务**（`pywin32.win32serviceutil`），更符合企业运维规范；服务本身即开机自启，与 schtasks 为替代关系 |
| **多语言国际化** | 中文硬编码 | 第三篇 i18n 已抽到 `i18n/`，GUI 文案走 `tr()`/字典查找 |
| **TLS 加密** | token 明文传输（LAN 可信） | 可选自签名 TLS（`websockets`/`aiohttp` 支持 `ssl`），增强安全性 |
| **Web 化（Electron）** | Host 当前为 PyQt5 原生 GUI | 未来若需 Web 化，再迁移到 Electron + Vue/React（§6.2 备选）；本版本不实施 |

---

## 23. 文档维护约定

### 23.1 目的

为避免文档碎片化，本项目统一以本文件为唯一主文档。后续所有新增需求、设计、规格均追加到对应篇章。

### 23.2 命名与章节规划

- 主文档：`README.md`（唯一主文档）
- 篇章划分：
  - **第一篇** 系统技术规格（架构 / 协议 / 数据格式 / 采集 / 部署 / 运维 / API）
  - **第二篇** 需求增强说明（历史增强点与决策）
  - **第三篇** 多语言 i18n
  - **第四篇** 自定义红线告警
  - **后续新需求** → 追加为新篇章（如「第五篇 · XX功能」「第六篇 · YY功能」），并更新目录

### 23.3 新增需求规范

1. 新需求先在对应篇章下新增小节（如 `### X.Y 需求名`）。
2. 若需求为全新主题，新增篇章并更新本目录。
3. 文档中代码示例与实现保持一致；实现变更时同步更新文档。
4. 验收清单逐条可勾选，作为实施完成依据。

---

## 24. 自检脚本与验收

### 24.1 自检脚本

```
python tests/test_p0.py        # 协议/鉴权/链路/发现/评分器/采集器冒烟（42 通过/3 跳过，缺 PyQt5）
python tests/test_api.py       # （v5.0 主测试）Agent REST /api/* + WebSocket 订阅端到端（14 项）
python tests/test_connect.py   # v4.0 遗留，已弃用（SKIP，改用 test_api.py）
python tests/test_p4.py        # v4.0 遗留，已弃用（SKIP，改用 test_api.py）
```

> **v5.0 测试策略**：`test_api.py` 是当前主测试（覆盖 Agent REST + WebSocket 全链路）。`test_connect.py` / `test_p4.py` 为 v4.0 遗留（基于已删除的 `node/` TCP 架构），运行即 SKIP，保留仅作历史参考。

> **v5.0 状态**：`test_api.py` **14/14 通过**（M2 交付）；Host WS 客户端沙箱端到端 **8/8 通过**（M3 交付）；Agent 本机仪表盘 stub 验证通过（M2b）。`test_p0`/`test_connect` 因采集器迁至 `common/` 已保持通过（53/53、17/17）；`test_p4` 的 T1 段通过、T2 段需 PyQt5（当前环境缺）。后续 M4/M5 迁移时适配新协议（WS 替代 TCP）。

### 24.2 v5.0 验收清单

- [ ] **副机端 Agent** 可独立运行，提供 WebSocket（`/ws`）和 REST（`/api/*`）服务。
- [ ] **主机端 Host** 通过 WebSocket 连接 Agent，实时显示数据，**延迟 < 1 秒**。
- [ ] Host 同时连接多台 Agent，节点列表正确展示各节点状态。
- [ ] 所有原有采集指标正常显示（CPU/GPU/内存/磁盘/网络/帧率/进程/温度/网络质量评分），阈值变色、告警生效。
- [ ] REST API（health/nodes/scan/config）可用，token 鉴权生效。
- [ ] mDNS 自动发现可用（可选）；手动添加支持。
- [ ] **断线重连**：Agent 断开后 Host 自动重连（指数退避），重连后数据流恢复；多 Agent 同时断线时互不影响（§4.6 / §19.7）。
- [ ] Agent 本机仪表盘（若有）正常工作。
- [ ] 开机自启、单实例、日志轮转等运维功能正常。
- [ ] 自检脚本覆盖核心通信和采集。
- [ ] 旧 `node/`、`client/` 角色相关文档描述已移除（本文档已无 Node 角色）。
- [ ] **Agent 与 Host 独立打包**：产出两个独立安装包（Agent-Setup / Host-Setup），默认安装目录分离（§16.5）。
- [ ] 安装互不干扰：注册表/计划任务/快捷方式带角色后缀；同一台电脑可同时运行 Agent 与 Host（§16.5.3）。

---

## 25. v5.0 迁移实施步骤

### 25.1 M1 · 抽取采集器到公共位置 ✅

- 将 `node/collectors/` 迁入 `common/collectors/`，供 Agent 与 Host 本机节点共用。
- 修改各端 import 路径，运行 `test_p0.py` 确认采集器冒烟仍通过。
- `SelfMonitor` 从 `host/` 提升至 `common/self_monitor.py`（`host/self_monitor.py` 保留为转发，消除 agent→host 反向依赖）。

### 25.2 M2 · 实现 Agent 服务 ✅

- 基于 `aiohttp` 单应用实现 REST + WebSocket（同端口 12345）。
- `aggregator.py`：每秒聚合，写入线程安全的最新帧缓存（不再是直接 broadcast）。
- `websocket_server.py`：`/ws` 多订阅推送 + 鉴权（查询参数 `?token=` 首选，首帧 auth 备选）+ PING/PONG + `loss_ping`/`loss_pong`。
- `http_server.py`：`/api/health` `/api/nodes` `/api/scan` `/api/config`（token 不可经 API 修改）。
- `discovery.py`：UDP/mDNS 广播与注册（Agent 自实现，不依赖 node/）。
- `self_monitor.py`：性能兜底（复用 `common/self_monitor.py`）。
- `main.py`：`python -m agent` 入口（单实例、端口检测、asyncio 事件循环、退出清理）。
- **自测**：`tests/test_api.py` **14/14 通过**。

### 25.2b M2b · Agent 本机仪表盘 ✅

- 新增 `agent/gui/`：`main_window.py`（`AgentDashboardWindow`）——本机全部采集数据分区显示（复用 `host/gui/detail_panel.DetailPanel`）、连接信息区（IP/端口/Token/连接串一键复制）、后台服务状态（订阅者数）。
- 本地采集直供 GUI（复用 `host/local_node.LocalCollectorPack`，不经网络），与推送数据同构。
- `agent/main.py` 新增 `--gui` 参数：**默认后台模式**（无界面，pythonw 运行）；`--gui` 时 Qt 主循环 + 后台 asyncio 服务在 QThread 中运行，关闭窗口即停服务。
- **自测**：stub PyQt5 验证导入/实例化/数据刷新通过。

### 25.3 M3 · Host 前端改造 ✅

- **`host/connection.py` 重写为 WebSocket 客户端**：`NodeConnection` 改用 `websocket-client` 连接 `ws://<ip>:<port>/ws?token=xxx`。
  - 类名与信号（`data_received/status_changed/rtt_updated/loss_updated`）**与 v4.0 完全兼容**，`host/gui` 零改动装配。
  - 鉴权：URL 查询参数（Agent 握手阶段校验，§4.4 推荐方式）。
  - RTT：WS PING 保活 + `loss_ping`/`loss_pong` 回显 `perf_counter` 时间戳精确计算（精度 < 1ms）。
  - 丢包：每 10 秒 3 个应用层 `loss_ping`（§4.7 低频补充）。
  - 断线独立指数退避重连（1s→60s）。
- 复用现有 GUI（节点列表/详情/概览/变色）、红线告警（`host/alerts.py`）、i18n——均未改动。
- **自测**：沙箱端到端（stub PyQt5 + 真实 Agent）**8/8 通过**（连接/收帧/字段/RTT/鉴权失败）。

### 25.4 M4 · 便捷连接与鉴权迁移

- mDNS/连接码/.pcm/剪贴板逻辑收敛到 `common/connect_code.py`（沿用）。
- 鉴权改为 WS 查询参数/首帧 auth + REST Bearer 头。
- RTT 改用 WebSocket PING/PONG 帧。

### 25.5 M5 · 打包与验收（2 天）

> **强制双端分离**：Agent 和 Host **分别打包**，产出**两个独立安装包**。构建系统、输出产物、安装目录、发布命名等**全部规定集中在 §16.5**，本节只列 M5 的落地动作，不重复约束细节。

- **Agent 打包**：`build_agent.py` 基于 `agent.spec` 产出 `PC-Monitor-Agent-v5.0-win-x64.exe`，支持 `--install-startup`。
- **Host 打包**：`build_host.py`（PyInstaller `host.spec`）产出 `PC-Monitor-Host-v5.0-win-x64.exe`。
- **独立触发与发布**：两个构建脚本各自独立触发；CI/CD 分别产出两个制品，发布到不同目录/标签。
- **更新部署文档**：分别说明 Agent 与 Host 的安装、防火墙放行、开机自启配置（§16.2 / §16.3 / §13）。
- **提供独立 API 文档**：Swagger/OpenAPI 文件放 `docs/api.yaml`，供第三方前端集成（§20）。
- **运行自检脚本**：`test_p0`、`test_connect`、`test_p4`、`test_api`（新增），确保各自模块通过（§24.1）。
- **验收**：按 §16.5.4 打包期检查清单与 §24.2 验收清单逐项确认。

---

# 第三篇 · 多语言支持（i18n）

> 版本：v5.0　　日期：2026-08-10　　适用：局域网硬件监控系统（v5.0 前后端分离版）
> 状态：**设计稿 · 待评审**（评审通过后进入实施）

---

## 1. 背景与目标

### 1.1 现状

当前系统 GUI 文案为**中文硬编码**，散布于各界面组件：

- `host/gui/` — 主机端（主窗口 / 节点列表 / 详情面板 / 概览网格 / 自动发现弹窗）
- `agent/gui/main_window.py` — Agent 本机仪表盘（原生 PyQt5，`--gui` 模式）
- `common/connect_dialog.py` — 便捷连接对话框（连接码 / 剪贴板 / 首屏引导）

统计：约 **3800+ 中文字**分布在界面文件中，约 150 条用户可见文案。

### 1.2 需求（v2 更新，v5.0 沿用）

| 需求 | 说明 |
|------|------|
| **语言范围** | **中英双语**，支持切换 |
| **语言选择方式** | **启动时弹窗**让用户选择（中文 / English），记忆选择 |
| **覆盖范围** | 所有**用户可见**文案：按钮 / 标签 / 标题 / 提示框 / 状态栏 / 菜单 / 右键菜单 / tooltip |
| **不翻译** | 程序内部标识（type 字段、config key）、技术名词（IP / TCP / GPU / CPU / Token / RTT / API） |

### 1.3 设计原则

1. **单一来源**：文案集中在 `i18n/zh_CN.json` + `i18n/en.json`，界面不写死。
2. **Key 化引用**：代码通过 `tr("key")` 取文案。
3. **最小侵入**：只改 GUI 层文案引用，不动采集/网络逻辑。
4. **启动选择 + 记忆**：首次启动弹语言选择窗，写入配置；后续启动读配置，不再弹。
5. **可重选**：设置中提供"语言"入口（可选，至少支持改配置重启）。

---

## 2. 架构设计

### 2.1 模块划分

```
common/
└── i18n.py                  # 国际化核心：加载/查询/语言选择弹窗
i18n/
├── zh_CN.json               # 中文文案
└── en.json                  # 英文文案
```

### 2.2 文案资源格式

两份 JSON，key 完全一致，值分别为中/英文。

`i18n/en.json`：
```json
{
  "app.title.host": "PC Monitor - Host",
  "topbar.connected": "Connected {n} / {total} nodes",
  "topbar.add_node": "Add Node",
  "metric.cpu_usage": "CPU Usage",
  "dialog.confirm_exit": "Exit PC Monitor?",
  "lang.select.title": "Select Language",
  "lang.select.prompt": "Please choose your language:",
  "lang.zh_CN": "中文",
  "lang.en": "English"
}
```

`i18n/zh_CN.json`（同 key）：
```json
{
  "app.title.host": "PC 监控 - 主机端",
  "topbar.connected": "已连接 {n} / {total} 节点",
  "topbar.add_node": "添加节点",
  "metric.cpu_usage": "CPU 使用率",
  "dialog.confirm_exit": "确定退出 PC 监控？",
  "lang.select.title": "选择语言",
  "lang.select.prompt": "请选择您的语言：",
  "lang.zh_CN": "中文",
  "lang.en": "English"
}
```

> **命名规范**：`区域.组件.含义`，如 `metric.cpu_usage`、`dialog.confirm_exit`。两份文件 key 必须一致（有校验工具可查）。

### 2.3 核心接口

```python
# common/i18n.py
import json
import os

_lang = "zh_CN"
_strings = {}

def load_language(lang: str) -> None:
    """加载语言资源；缺失回退 zh_CN。"""
    global _lang, _strings
    _lang = lang if lang in ("zh_CN", "en") else "zh_CN"
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "i18n", f"{_lang}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _strings = json.load(f)
    except FileNotFoundError:
        _strings = {}
        if _lang != "zh_CN":
            load_language("zh_CN")

def tr(key: str, *args) -> str:
    """按 key 取文案；key 不存在回退 key 本身。"""
    text = _strings.get(key, key)
    if args:
        try:
            return text.format(*args)
        except (IndexError, KeyError):
            return text
    return text

def get_lang() -> str:
    return _lang
```

### 2.4 语言选择弹窗（启动时）

首次启动（配置无 `language` 字段）时，在创建主窗口**前**弹出选择框：

```python
# common/i18n.py 内
def choose_language_dialog(parent=None) -> str:
    """弹窗让用户选择语言，返回 'zh_CN' / 'en'。默认中文。"""
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox

    dialog = QDialog(parent)
    dialog.setWindowTitle("选择语言 / Select Language")
    layout = QVBoxLayout(dialog)
    label = QLabel("请选择语言 / Please choose your language:")
    layout.addWidget(label)

    btn_zh = QPushButton("中文")
    btn_en = QPushButton("English")
    result = {"lang": "zh_CN"}

    def choose(lang):
        result["lang"] = lang
        dialog.accept()

    btn_zh.clicked.connect(lambda: choose("zh_CN"))
    btn_en.clicked.connect(lambda: choose("en"))
    layout.addWidget(btn_zh)
    layout.addWidget(btn_en)
    dialog.exec_()
    return result["lang"]
```

> **弹窗时序**（关键）：语言选择弹窗必须在 `load_language()` **之前**创建控件文案（按钮上写"中文/English"是固定的，不需要翻译），选定后 `load_language(lang)` 再创建主窗口。因此弹窗自身文案固定双语显示。

### 2.5 启动流程（host / agent 一致）

```
main()
  ├─ 解析参数（--install-startup 等）
  ├─ 单实例检测
  ├─ 初始化日志
  ├─ 加载配置 cfg
  ├─ app = QApplication(...)          # 仅 GUI 端；Agent 无 GUI 时跳过
  ├─ 语言处理：
  │     if "language" not in cfg:        # 首次启动
  │         lang = choose_language_dialog(app)   # 弹窗选择
  │         cfg["language"] = lang               # 写入配置
  │         save_config(cfg)
  │     else:
  │         lang = cfg["language"]
  │     load_language(lang)              # 加载文案资源
  ├─ app.setStyleSheet(DARK_QSS)
  ├─ window = HostMainWindow(cfg) / AgentDashboard(cfg)   # 主窗口用已加载语言
  └─ window.show(); app.exec_()
```

> Agent 默认无界面（后台服务）；仅当其启用本机仪表盘（Qt 版）时才需要接入 i18n。Web 版仪表盘在 HTML 内做前端 i18n（同 key 策略）。

---

## 3. 迁移方案（实施步骤）

### 3.1 迁移范围清单

| 文件 | 主要内容 | 预计文案数 |
|------|----------|-----------|
| `host/gui/main_window.py` | 顶栏/按钮/菜单/右键/对话框/状态 | ~35 |
| `host/gui/node_list.py` | 节点项标签/右键菜单 | ~10 |
| `host/gui/detail_panel.py` | 指标卡标签/头部 | ~15 |
| `host/gui/overview_grid.py` | 卡片标签/计数 | ~8 |
| `host/gui/discovery_dialog.py` | 扫描弹窗 | ~8 |
| `agent/gui/main_window.py` | 本机仪表盘（可选，PyQt5） | ~12 |
| `common/connect_dialog.py` | 连接码/剪贴板/首屏引导 | ~18 |

### 3.2 迁移步骤

1. 建 `i18n/en.json` + `i18n/zh_CN.json`（key 一致）。
2. 建 `common/i18n.py`（含 `load_language`/`tr`/`choose_language_dialog`）。
3. `host/main.py`（及可选 `agent/gui/main_window.py`）接入语言选择流程。
4. 逐个 GUI 文件把中文硬编码替换为 `tr("...")`。
5. 全局扫描中文残留，确认用户可见文案全覆盖。
6. 验证：首次启动弹语言选择、选后界面语言正确、配置记忆、重启不弹。

### 3.3 工具链辅助

- 一次性脚本 `scripts/scan_i18n.py`：扫描 `.py` 引号内中文字符串，输出未迁移清单。
- 校验 `zh_CN.json` 与 `en.json` 的 key 集合一致。

---

## 4. 语言持久化

### 4.1 配置字段

各端配置文件增加：

```json
"language": "zh_CN"   // 或 "en"
```

- 首次启动无此字段 → 弹语言选择 → 写入。
- 后续启动读配置，不弹窗。
- 用户改配置重启即可切换。

### 4.2 未来扩展（预留）

- 加语言 → 新建 `i18n/xx.json` + 弹窗加按钮。
- 运行时热切换 → 设置页下拉 + `load_language()` + 重建窗口。

---

## 5. 兼容性与风险

| 项 | 说明 |
|----|------|
| **核心逻辑不受影响** | i18n 只改 GUI 文案引用 |
| **key 泄漏** | `tr` 未找到 key 回退显示 key 本身，不崩溃 |
| **占位符** | 用 `{0}/{1}` 格式化，避免 `%s` 与 JSON 转义冲突 |
| **弹窗时序** | 语言选择弹窗按钮固定双语，选定后才加载文案建主窗口 |
| **Agent 无界面** | Agent 后台默认不建 QApplication，不触发语言弹窗；仅仪表盘启用时接入 |
| **日志/协议** | 不翻译：type、日志、配置内容、内部中文注释保留 |

---

## 6. 验收清单

- [ ] `zh_CN.json` / `en.json` 覆盖全部用户可见文案，key 一致
- [ ] 首次启动弹语言选择窗（中文/English）
- [ ] 选择后界面语言立即生效
- [ ] 语言写入配置，重启不弹，界面保持所选语言
- [ ] Host / Agent 仪表盘界面无**另一种语言残留**
- [ ] 按钮/标签/标题/提示框/菜单/右键/tooltip 全部正确
- [ ] 占位符文案（"Connected 3/4 nodes" / "已连接 3/4 节点"）格式正确
- [ ] `tr` 无 key 泄漏
- [ ] 自检 `tests/test_p0.py` 仍全部通过

---

## 7. 工作量评估

| 阶段 | 内容 | 相对工作量 |
|------|------|-----------|
| 1 | 建 `en.json` + `zh_CN.json` + `i18n.py` | 小 |
| 2 | 语言选择弹窗 + Host 接入 | 小 |
| 3 | GUI 文件文案替换 | **主要**（约 150 处） |
| 4 | 残留扫描 + 验证 + 测试 | 中 |

---

# 第四篇 · 自定义数值红线告警

> 版本：v5.0　　日期：2026-08-10　　适用：局域网硬件监控系统（v5.0 前后端分离版）
> 状态：**设计稿 · 待评审**（评审通过后进入实施）

---

## 1. 背景与目标

### 1.1 现状

当前系统阈值变色是**内置固定**的（`common/theme.py` §14.1）：CPU/GPU/内存使用率、温度、磁盘、评分、RTT 各有固定绿/橙/红阈值。但存在不足：

1. **阈值不可配**：用户无法自定义，如希望"CPU 超过 60% 就告警"（而非默认 80%）。
2. **只变色不告警**：仅界面数值变色，无显式告警提示（弹窗/状态栏/日志）。
3. **无用户告警**：无法针对特定指标设置"红线"，触线即引起注意。

### 1.2 需求

| 需求 | 说明 |
|------|------|
| **自定义红线** | 用户可配置任意指标的**红线阈值**，数值触及/超过即告警 |
| **告警方式** | 状态栏横幅 + 日志 + 界面数值高亮（红/橙） |
| **配置持久化** | 红线配置写入 `host_config.json`（或独立 `alerts.json`） |
| **检测位置** | **Host 前端检测**为主（对收到的每帧数据本地判定）；也可由 Agent 后端推送告警（可选） |
| **范围** | Host 端（集中大屏）为主；Agent 本机仪表盘可复用 `AlertEngine` |
| **不强制** | 未配置红线的指标沿用内置阈值变色 |

### 1.3 设计原则

1. **配置驱动**：红线从配置文件读取，改配置重启生效（不做运行时热编辑）。
2. **通用指标路径**：用 `section.key` 定位任意指标（如 `cpu.total_usage`、`gpu.core_temp_c`）。
3. **内置默认**：未配置时行为与现在一致（内置阈值变色，无告警）。
4. **轻量**：告警检测在数据更新时同步做，不增加独立线程/协程。

> **v5.0 说明**：告警检测默认在 **Host 前端**对每帧 `monitor_data` 本地判定（`host/alerts.py`）。若希望多端告警一致，也可在 Agent 后端实现同一 `AlertEngine`，将告警随 WS 帧或独立 `alert` 消息推送；两种方式可并存，前端判定延迟更低、无需改协议。

---

## 2. 配置设计

### 2.1 配置格式

在 `host_config.json` 增加 `alerts` 段（数组，每项一个红线规则）：

```json
{
  "alerts": [
    { "path": "cpu.total_usage", "name": "CPU 使用率", "red": 90, "warn": 80 },
    { "path": "gpu.core_temp_c", "name": "GPU 温度", "red": 85, "warn": 80 },
    { "path": "ram.usage_percent", "name": "内存", "red": 90 },
    { "path": "disk[0].usage_percent", "name": "系统盘", "red": 95 },
    { "path": "fps.fps", "name": "帧率", "red_min": 30, "warn_min": 60 }
  ]
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `path` | ✅ | 指标定位路径，`section.key`（见 2.2） |
| `name` | ❌ | 显示名；缺省用 path 末段 |
| `red` / `warn` | 二者至少一 | **上限红线**：数值 > red 触发红色告警；> warn 触发橙色预警（可选） |
| `red_min` / `warn_min` | 二者至少一 | **下限红线**：数值 < red_min 触发红色告警（如 FPS 低于 30） |

> 优先级：`red`/`warn`（上限）与 `red_min`/`warn_min`（下限）可同时配置；同一指标同时配上限+下限时分别判定，取更高告警级。

### 2.2 指标路径约定

`path` 用点号分隔，支持数组索引：

| path | 含义 |
|------|------|
| `cpu.total_usage` | frame["cpu"]["total_usage"] |
| `cpu.package_temp_c` | CPU 温度 |
| `gpu.core_temp_c` | GPU 温度 |
| `ram.usage_percent` | 内存使用率 |
| `net_quality.quality_score` | 网络评分 |
| `fps.fps` | 帧率 |
| `disk[0].usage_percent` | 第一个盘符使用率 |

### 2.3 内置默认红线（参考行业监控标准）

```json
{
  "alerts": [
    { "path": "cpu.total_usage", "name": "CPU 使用率", "red": 95, "warn": 80 },
    { "path": "gpu.usage_percent", "name": "GPU 使用率", "red": 95, "warn": 80 },
    { "path": "ram.usage_percent", "name": "内存", "red": 90, "warn": 80 },
    { "path": "cpu.package_temp_c", "name": "CPU 温度", "red": 90, "warn": 80 },
    { "path": "gpu.core_temp_c", "name": "GPU 温度", "red": 90, "warn": 80 },
    { "path": "gpu.hotspot_temp_c", "name": "GPU 热点", "red": 105, "warn": 95 },
    { "path": "disk[0].usage_percent", "name": "系统盘", "red": 95, "warn": 85 },
    { "path": "net_quality.quality_score", "name": "网络评分", "red_min": 50, "warn_min": 60 }
  ]
}
```

> 阈值依据（行业参考）：
> - **CPU/GPU 温度**：警戒 80-85°C，危险 90°C+（长时间 >90°C 有降频/损坏风险）
> - **GPU 热点温度（Hotspot）**：警戒 95°C，危险 105°C（NVIDIA/AMD 设计上限通常 100-110°C）
> - **使用率**：CPU/GPU 80% 警戒、95% 危险；内存 80% 警戒、90% 危险
> - **磁盘**：85% 警戒、95% 危险（接近满盘性能下降）
> - **网络评分**：60 以下注意、50 以下较差

> 若 `alerts` 缺失 → 使用内置默认（同 §14.1 阈值，但显式告警）；`"alerts": []` → 完全关闭红线告警。

---

## 3. 检测逻辑

### 3.1 告警引擎（核心）

新增 `host/alerts.py`：

```python
class AlertEngine:
    """红线告警引擎：根据配置检测指标是否越线。"""

    def __init__(self, rules):
        # rules: 解析后的规则列表
        self.rules = rules

    def check(self, frame: dict) -> list:
        """
        对一帧数据检测所有规则，返回告警列表。
        :return: [{"name", "path", "value", "level"}]
                 level: "red" / "warn"
        """
        alerts = []
        for rule in self.rules:
            value = extract_path(frame, rule["path"])
            if value in (None, "N/A"):
                continue
            level = self._judge(rule, value)
            if level:
                alerts.append({
                    "name": rule["name"],
                    "path": rule["path"],
                    "value": value,
                    "level": level,
                    "threshold": rule.get("red") or rule.get("red_min") or
                                 rule.get("warn") or rule.get("warn_min"),
                })
        return alerts

    def _judge(self, rule, value) -> str | None:
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None
        # 上限
        if "red" in rule and v > rule["red"]:
            return "red"
        if "warn" in rule and v > rule["warn"]:
            return "warn"
        # 下限
        if "red_min" in rule and v < rule["red_min"]:
            return "red"
        if "warn_min" in rule and v < rule["warn_min"]:
            return "warn"
        return None


def extract_path(frame: dict, path: str):
    """按 'section.key' 或 'disk[0].key' 提取指标值。"""
    if "[" in path:
        head, rest = path.split("]", 1)
        section = head.split("[")[0]
        idx = int(head.split("[")[1])
        sub = rest.lstrip(".")
        try:
            return frame[section][idx].get(sub)
        except (KeyError, IndexError, TypeError):
            return None
    section, _, key = path.partition(".")
    try:
        return frame.get(section, {}).get(key)
    except (AttributeError, TypeError):
        return None
```

### 3.2 主窗口集成

`HostMainWindow` 数据更新时调用：

```python
def _on_data(self, frame, node_id):
    # ... 现有更新逻辑 ...

    # 红线告警检测（对收到的每帧数据）
    alerts = self.alert_engine.check(frame)
    self._show_alerts(alerts, node_id)
```

**告警聚合展示**：
- 维护 `self.current_alerts`（最近一帧的告警集）。
- 有 red 告警 → 状态栏红色提示 + 日志 WARNING。
- 有 warn 告警 → 状态栏橙色提示 + 日志 INFO。

### 3.3 告警展示（三种方式全开）

| 位置 | 展示 | 触发 |
|------|------|------|
| **状态栏** | `⚠ CPU 使用率 96% 超红线`（红色文字） | 每帧检测到告警即更新 |
| **日志** | `WARNING [alert] CPU 使用率 96% > 红线 90` | red → WARNING，warn → INFO |
| **弹窗提示** | 系统托盘气泡（`QSystemTrayIcon.showMessage`） | red 告警触发时弹出（warn 不弹，避免频繁打扰） |

**弹窗设计**：
- 使用系统托盘图标（`QSystemTrayIcon`），程序运行时驻留托盘。
- red 告警首次触发时弹出气泡：`⚠ CPU 使用率 96% 超红线`。
- **去重**：同一指标同一节点从"正常→red"状态变化时弹一次；持续 red 不重复弹（记录上一状态）。
- 未安装托盘/禁用时降级：仅状态栏 + 日志。
- 配置 `"alert_popup": true`（默认 true）可关闭弹窗。

---

## 4. 配置文件加载与校验

### 4.1 加载

`host/config.py` 增加：

```python
def load_alerts(cfg) -> list:
    """从配置加载红线规则；缺失用内置默认。"""
    if "alerts" in cfg and cfg["alerts"] is not None:
        return cfg["alerts"]
    return DEFAULT_ALERTS  # 内置默认
```

### 4.2 校验

- `path` 格式合法（`section.key` 或 `section[idx].key`）。
- `red/warn/red_min/warn_min` 为数值。
- 非法规则跳过并日志警告，不影响其他规则。

---

## 5. 范围

- **Host 端实施**：`HostMainWindow` 集成告警检测与展示（前端检测）。
- Agent 本机仪表盘**预留**：`AlertEngine` 设计为通用（接收 frame + rules），未来可在 Agent 端复用或后端推送告警；本期不强制接入。

---

## 6. 兼容性与风险

| 项 | 说明 |
|----|------|
| **不破坏现有变色** | 红线告警是**叠加**：即使无配置，内置阈值变色仍生效 |
| **性能** | 每帧检测若干规则，纯字典查找 + 数值比较，开销可忽略 |
| **N/A 处理** | 指标为 N/A 时跳过检测 |
| **旧配置兼容** | 无 `alerts` 字段 → 用内置默认，不影响现有用户 |
| **多节点** | 告警按节点聚合，每节点独立判定 |
| **弹窗去重** | 状态变化才弹，持续告警不重复打扰 |

---

## 7. 验收清单

- [ ] 未配置 `alerts` 时，内置默认红线生效（CPU/GPU/内存/温度/磁盘/评分）
- [ ] 配置自定义红线后，数值越线**状态栏**告警（红/橙）
- [ ] 下限红线（如 FPS < 30）生效
- [ ] red 告警触发**系统托盘气泡**弹窗（去重：状态变化弹一次）
- [ ] 告警日志级别正确（red→WARNING，warn→INFO）
- [ ] N/A 值不触发告警
- [ ] 非法配置规则被跳过并日志提示
- [ ] 自检 `tests/test_p0.py` 仍全部通过

---

## 8. 工作量评估

| 阶段 | 内容 | 相对工作量 |
|------|------|-----------|
| 1 | `host/alerts.py`（AlertEngine + extract_path） | 小 |
| 2 | `host/config.py` 加载/默认/校验 | 小 |
| 3 | `HostMainWindow` 集成（状态栏 + 日志 + 托盘弹窗） | **中** |
| 4 | 托盘图标 + 去重逻辑 | 中 |
| 5 | 配置示例 + 测试 | 小 |

---

**实现总结**：v5.0 前后端分离架构下，Agent 为服务端（采集 + WebSocket/REST 推送 + 可选仪表盘），Host 为纯前端（订阅展示 + 节点管理 + 红线告警 + i18n）。数据帧格式沿用 v4.0 `monitor_data`，实现按 §25 M1-M5 逐步迁移。详见 §1-§25 与各篇章。

---

> 文档结束。后续更新请在对应篇章内修改，勿另建文档。

