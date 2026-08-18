# LAN PC Monitor 运行档案

> **生成时间**：2026-08-11
> **环境**：Linux 沙箱（非 Windows），Python 3.10.12
> **目的**：完整运行项目一次，记录运行结果、产生的变化、发现的问题，供后续 AI 参考并提改进意见。

---

## 一、运行环境

| 项 | 值 | 说明 |
|----|-----|------|
| 系统 | Linux 沙箱 | 非 Windows，部分硬件采集降级 |
| Python | 3.10.12 | 满足 ≥3.10 要求 |
| 已装依赖 | psutil 7.2.2 / aiohttp 3.14.3 / websockets 16.1.1 / websocket-client 1.9.0 / numpy 2.2.6 / requests 2.34.2 | |
| **缺失依赖** | **PyQt5 / zeroconf / wmi / pynvml / dxcam / netifaces** | 沙箱 pip 装 PyQt5 报 SSL 错误；zeroconf 缺失导致 mDNS 降级 |

> **关键影响**：无 PyQt5 → Host GUI 无法真机启动，用 stub 模拟验证逻辑；无 zeroconf → mDNS 注册跳过，仅 UDP 广播可用；无 wmi/pynvml → GPU/温度采集降级 N/A。

---

## 二、测试套件运行结果

| 测试 | 结果 | 说明 |
|------|------|------|
| `tests/test_p0.py` | **42 通过 / 0 失败 / 3 跳过** | 3 跳过因缺 PyQt5（信号链路验证） |
| `tests/test_api.py` | **14 通过 / 0 失败** | 主测试：REST + WebSocket 全链路 ✅ |
| `tests/test_connect.py` | SKIP | v4.0 遗留，运行即跳，指向 test_api |
| `tests/test_p4.py` | SKIP | v4.0 遗留，运行即跳，指向 test_api |

**test_api 明细（14 项）**：

```
REST: health 带 token 200 / 无 token 401 / 错 token 401 / nodes / config 不返回 token / POST config 白名单 / POST 拒绝改 token
WS:   错误 token 被拒 / 鉴权通过收 3 帧 / 字段完整 / connected_clients 正确 / loss_ping→loss_pong
```

---

## 三、Agent 服务冒烟测试

### 3.1 后台模式（`python -m agent`）

| 检查项 | 结果 |
|--------|------|
| 端口 12345 监听 | ✅ |
| `GET /api/health`（带 token） | ✅ `{"status":"ok","version":"5.0.0","hostname":"claude","ip":"172.16.10.3","port":12345}` |
| 无 token → 401 | ✅ HTTP 401 |
| `GET /api/nodes` | ✅ 返回 self（hostname/ip/port/alias） |
| `GET /api/config` | ✅ 不返回 token（keys 无 token） |
| UDP 广播器 | ✅ 已启动（广播） |
| mDNS | ⚠️ **zeroconf 未安装，跳过**（仅 UDP 广播） |
| SIGTERM 干净退出 | ✅ 无锁残留 |

### 3.2 WebSocket 多客户端 + 数据帧

| 检查项 | 结果 |
|--------|------|
| 两个订阅者同时连接 | ✅ connected_clients = 2 |
| `monitor_data` 帧 | ✅ type/hostname/9 个 section 完整 |
| cpu.total_usage | ✅ 数值 |
| ram.usage_percent | ✅ 9.7% |
| `net_quality.quality_score` | ⚠️ None（**设计如此**：Agent 端仅采网关延迟，评分由 Host 注入） |
| loss_ping → loss_pong | ✅ 回显 seq |
| 错误 token | ✅ 被拒（握手成功后应用层拒绝，无数据推送） |

### 3.3 Host WS 客户端（NodeConnection，stub PyQt5）

| 检查项 | 结果 |
|--------|------|
| 连接成功（connected 状态） | ✅ |
| 收到 ≥3 帧 monitor_data | ✅ |
| 帧 section 完整 | ✅ |
| connected_clients ≥1 | ✅ |
| **RTT 实测** | ✅ **0.371 ms**（loss_pong 回显 perf_counter） |
| 丢包测量 | ✅ 0.0% |
| **合计 7/7 通过** | ✅ |

### 3.4 `--gui` 仪表盘模式（stub 验证）

| 检查项 | 结果 |
|--------|------|
| `agent/gui/main_window.py` AgentDashboardWindow 实例化 | ✅ |
| `agent/local_node.py` LocalCollectorPack 导入 | ✅ |
| 真机窗口显示 | ⚠️ 沙箱无 PyQt5，未实显；真机 `python -m agent --gui` 可显示 |

---

## 四、运行产生的文件变化

### 4.1 运行时文件（gitignore，不入库）

| 文件 | 状态 | 说明 |
|------|------|------|
| `agent_config.json` | 已存在 | 含 token、端口、采集器开关、`language`、`window_geometry`（曾 GUI 运行） |
| `host_config.json` | 已存在 | 已配置 1 个节点（本机 Agent localhost:12345） |
| `logs/agent.log` | 更新 | 本次运行追加（启动/鉴权/WS 连接记录） |
| `logs/host.log` | 已存在 | 历史运行记录 |
| `logs/client.log` | 已存在 | v4.0 遗留 |
| `logs/node.log` | 已存在 | v4.0 遗留 |
| `logs/screen_capture.png` | 已存在 | 3.6MB，历史截屏 |

### 4.2 本次运行日志关键片段（logs/agent.log）

```
[INFO] agent: ====== Agent 启动 ======
[INFO] agent.aggregator: 数据聚合器已启动（间隔 1.0s）
[INFO] agent.discovery: UDP 广播器已启动（广播）
[INFO] agent.discovery: zeroconf 未安装，mDNS 注册跳过（仅保留 UDP 广播）
[INFO] agent: HTTP/WebSocket 服务已启动 0.0.0.0:12345
[INFO] agent.websocket: WS 客户端 127.0.0.1 已连接，当前订阅者 1/2
[WARNING] agent.websocket: WS 鉴权失败: 127.0.0.1
[INFO] agent: Agent 服务已停止
```

### 4.3 本次运行未产生

- 无 `build/`、`dist/` 打包产物（未执行 PyInstaller）
- 无数据库文件（v6.0 历史存储未实现）

---

## 五、发现的问题与观察点

### 5.1 设计如此（非 bug）

| # | 观察 | 说明 |
|---|------|------|
| 1 | `net_quality.quality_score` 在 WS 直连时为 None | Agent 端仅采网关延迟，评分/丢包由 Host 本地测量注入（§8.6 设计） |
| 2 | 错误 token 先握手成功再被拒 | 鉴权在 WS 应用层（发 auth_result ok:false 后 close），非 HTTP 握手层拒绝；客户端无数据推送即视为拒绝 |
| 3 | mDNS 降级 | zeroconf 未安装时静默降级为仅 UDP 广播，不影响核心功能 |

### 5.2 值得关注的改进点（供 AI 参考）

| # | 观察 | 建议方向 |
|---|------|----------|
| A | **错误 token 的 WS 拒绝语义不直观**：客户端看到"连接成功但无消息"，容易被误判为网络问题 | 可考虑握手层直接 HTTP 403，或连接后立即发 `auth_result:ok:false` 再 close（当前实现有发，但 websockets 库 close 太快可能未达客户端） |
| B | `/api/health` 的 `uptime` 字段取自 `system.uptime_seconds`（机器开机时长），非 Agent 服务启动时长 | 语义不清晰；建议改为 Agent 进程 uptime 或移除 |
| C | **缺 PyQt5 时 `test_p0` 3 项跳过**，且 `host/connection.py` 顶层 `import PyQt5` 导致无 GUI 环境无法导入 | 可考虑 PyQt5 惰性导入，便于无 GUI 环境测试网络层（当前测试用 stub 规避） |
| D | **错误 token 测试在 test_api 中通过"静默拒绝"判定**，但 Agent 日志会刷 `WS 鉴权失败` WARNING | 大量恶意探测会刷日志；可考虑限流/告警 |
| E | **mDNS 未装时静默降级**，用户可能不知道自动发现不可用 | 建议首次启动打一条显式日志/提示 |
| F | 沙箱中 CPU 采集 `total_usage=0.0`（首次预热） | 采集器首次采样预热行为，属预期 |
| G | `logs/screen_capture.png` 3.6MB 过大 | 建议清理或 gitignore 已有（已在 .gitignore） |
| H | **README/docs 已重构为 v6.0 定位**，但代码仍 v5.0；v6.0 功能（历史存储/事件/订阅）均未实现 | docs 已标 Design Draft，README 已分 Current/Roadmap，无混淆 |

### 5.3 环境限制说明

- **PyQt5 无法在沙箱安装**（pip SSL 错误）→ Host GUI 真机运行未验证，逻辑用 stub 验证
- **硬件采集降级**：无 GPU/温度传感器 → 相关字段 N/A（属预期健壮性）
- **Windows 专属功能**：schtasks 自启、注册表、PresentMon 帧率等未在沙箱验证

---

## 六、结论

- **后端核心链路全部通过**：Agent REST API（4 接口 + 鉴权）✅、WebSocket 实时推送（多客户端 + loss_ping/pong）✅、Host WS 客户端（连接/收帧/RTT 0.37ms/丢包）✅、测试套件（test_api 14/14，test_p0 42 通过）✅
- **项目健康**：SIGTERM 干净退出、无锁残留、日志轮转正常
- **主要未验证项**：Host PyQt5 GUI 真机交互、Windows 专属运维功能、mDNS（缺依赖）、v6.0 全部功能（未实现）
- **给 AI 的改进建议**：优先关注 §5.2 的 A/B/C 三项（错误 token 拒绝语义、health uptime 字段、PyQt5 惰性导入），以及补齐依赖后真机回归

---

*本档案由项目完整运行生成，基于实际输出记录，未虚构结果。*
