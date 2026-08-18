# 采集方案与算法

> **Version**: v5.0
> **Status**: Current
> **Compatibility**: 采集器实现细节，与 `monitor_data` Schema 对应

## 1. 各指标采集方案

采集方案对 Agent 与 Host 本机节点**完全一致**（共享 `common/collectors/`）。

### CPU

| 指标 | 方案 | 库 |
|------|------|-----|
| 总/每核使用率 | `psutil.cpu_percent(percpu=True)` | psutil |
| 频率 | `psutil.cpu_freq()` / WMI | psutil |
| 温度/功耗 | LibreHardwareMonitor (WMI) | 需管理员 |
| 核心数 | `psutil.cpu_count()` | psutil |
| 型号 | `cpuinfo.get_cpu_info()['brand_raw']` | py-cpuinfo |

### 内存

`psutil.virtual_memory()` + `psutil.swap_memory()`。

### GPU

按厂商三路，优先级 NVIDIA > AMD > Intel，任一可用即返回真实数据，全部不可用返回全 N/A。

#### NVIDIA（pynvml / NVML，主方案）

- 库：`nvidia-ml-py`（`import pynvml`），NVML 随驱动自带，无需 CUDA Toolkit。
- 字段 → NVML API：`usage_percent`（UtilizationRates.gpu）、`vram_used/total_mb`（MemoryInfo）、`core_temp_c`（Temperature GPU）、`hotspot_temp_c`（Temperature GPU_HOTSPOT，需 getattr fallback + LHM 补）、`core/mem_freq_mhz`（ClockInfo）、`power_w`（PowerUsage/1000）、`engine_usage`（Encoder/Decoder Utilization）。
- **关键健壮性**：新版 `usedGpuMemory` 可能返回 `None`，**必须判空**否则 `None/1024**2` 抛 TypeError 导致整个 GPU 采集失败。
- 多 GPU：默认采集 `index=0`，配置 `gpu_index` 指定。

#### AMD（pyadl，后备）

仅支持：`name`、`usage_percent`、`core_temp_c`、`core/mem_freq_mhz`。**实验性**——pyadl 多年未更新，较新驱动可能失效，采集器捕获初始化失败降级 N/A。

#### Intel（集显，降级）

返回全 N/A，仅 `name` 经 WMI `Win32_VideoController.Name` 取得。

#### GPU Top3 进程

NVIDIA 可用：`nvmlDeviceGetComputeRunningProcesses` 取 PID + `usedGpuMemory` → `psutil.Process(pid).name()`，按显存降序 Top3。

### 磁盘

- 读写速度/IOPS：`psutil.disk_io_counters` 1 秒差分
- 盘符↔物理盘映射：WMI `Win32_DiskDriveToDiskPartition` + `Win32_LogicalDiskToPartition`
- 队列深度：Performance Counter `\PhysicalDisk\Current Disk Queue Length`（docstring 需 raw string 防 `\P` 转义）
- 温度：LibreHardwareMonitor / smartctl（需管理员）
- 剩余空间：`psutil.disk_usage`

### 网络

`psutil.net_io_counters(pernic=True)` 差分；链接速度 WMI `Win32_NetworkAdapter.Speed`；错误/丢弃计数 `errin/errout/dropin/dropout`。

### 网络质量

- 到各 Host RTT：WebSocket PING/PONG（各 Host 独立测量）
- 到网关延迟：系统 `ping` 解析（兼容中英文）
- 丢包率：网关丢包 + WS 链路 loss_ping 补充
- 评分：见 §2，滑动平均

### 进程（2~3 秒采集）

CPU Top3（`psutil.process_iter` 排序）、GPU Top3（NVML PID + 判空）、uptime（`time.time() - boot_time()`）。

### 帧率

见 §3。

## 2. 网络质量评分算法

### 公式

```
延迟扣分 = max(0, (rtt_ms - 5) / 10) * 5      # 5ms 起算，每增 10ms 扣 5 分
丢包扣分 = packet_loss_percent * 10             # 每 1% 丢包扣 10 分
瞬时分   = max(0, round(100 - 延迟扣分 - 丢包扣分))
```

> 延迟扣分系数为 **5**（v3.0 曾用 15 导致延迟惩罚过重，回退为 5）。

### 校验

| rtt_ms | loss% | 瞬时分 | 等级 |
|--------|-------|--------|------|
| 1 | 0 | 100 | 优秀 |
| 15 | 0 | 95 | 优秀 |
| 30 | 1 | 78 | 良好 |
| 5 | 8 | 20 | 较差 |

### 滑动平均

显示分 = 最近 10 次瞬时分均值，平滑无线网络抖动。

### 等级

| 评分 | 等级 | 颜色 |
|------|------|------|
| ≥90 | 优秀 | 绿 |
| 70~89 | 良好 | 青绿 |
| 50~69 | 一般 | 橙 |
| <50 | 较差 | 红 |

## 3. 帧率采集方案

### 方案选择

| 方案 | 原理 | 适用 |
|------|------|------|
| **PresentMon CLI**（主） | ETW 捕获 Present 调用 | 有 exe + 管理员 |
| **DXGI 截帧**（降级） | dxcam 桌面帧差分估计 | 无 exe / 非管理员 |

选择逻辑：`collectors.fps == "presentmon"` 且 `tools/PresentMon.exe` 存在 + 管理员 → PresentMon；否则降级 DXGI；`"dxgi"` 强制 DXGI；`false` 不采集。

### 前台窗口动态绑定

`win32gui.GetForegroundWindow()` 取前台进程，PresentMon 按进程名捕获；窗口切换自动重启会话。

### 1% Low

最近 100 帧帧时间排序取第 99 百分位 → `low_1_percent = 1000 / p99`。

### 配置

```json
"collectors": {"fps": "presentmon"}   // presentmon | dxgi | false
```

> PresentMon.exe 需手动下载放入 `tools/`（GitHub: GameTechDev/PresentMon，MIT License）。
